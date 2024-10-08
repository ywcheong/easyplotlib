# https://realpython.com/python-pydantic
# ^ helpful link

import collections
import itertools
import uuid

from typing import List, Optional, Literal, Union, Any
from pydantic import (
    BaseModel,  # Base class
    ConfigDict,  # Configuration class
    ValidationInfo,  # For multi-field validation
    Field,  # For simple validation
    field_validator,  # For complex single validation
    model_validator,  # For complex overall validation
)

#################################################################
#   Reject - Exception
#################################################################


class CodeReject(Exception):
    def __init__(self, message):
        self.message = message


#################################################################
#   Figure
#################################################################


class FigureSize(BaseModel):
    model_config = ConfigDict(extra="forbid")
    row: int = Field(gt=0)
    column: int = Field(gt=0)


class FigureStyle(BaseModel):
    model_config = ConfigDict(extra="forbid")
    style_name: Optional[str]  # debug purpose attribute - not used


class Figure(BaseModel):
    model_config = ConfigDict(extra="forbid")
    size: FigureSize
    axes: List[List[Optional[str]]]
    style: FigureStyle

    # Check if Figure.axes.shape == (Figure.size.row, Figure.size.column)
    @model_validator(mode="after")
    def check_axes_dimension(self):
        row, column = self.size.row, self.size.column

        # check row-shape equality
        if row != len(self.axes):
            raise CodeReject(
                "Shape of figure.axes is not equivalent to the provided (row, column)"
            )

        # check column-shape equality
        for axes_row in self.axes:
            if column != len(axes_row):
                raise CodeReject(
                    "Shape of figure.axes is not equivalent to the provided (row, column)"
                )

        return self


#################################################################
#   Axes
#################################################################


class AxesStyle(BaseModel):
    model_config = ConfigDict(extra="forbid")
    style_name: Optional[str]  # debug purpose attribute - not used


class AxesElement(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str
    plot: List[str]
    style: AxesStyle


#################################################################
#   Plot.Data Format
#################################################################


class PlotData(BaseModel):
    relation: str
    model_config = ConfigDict(extra="forbid")

    def get_param_data_dict(self):
        result = dict()
        param_name_list = set(self.__dict__.keys()) - {"relation"}
        for param_name in param_name_list:
            result[param_name] = self.__dict__[param_name]
        return result


class SimplePlotData(PlotData):
    relation: Literal["plot"]
    x: str
    y: str


PlotDataSupported = Union[SimplePlotData]

#################################################################
#   Plot
#################################################################


class PlotStyle(BaseModel):
    model_config = ConfigDict(extra="forbid")
    style_name: Optional[str]  # debug purpose attribute - not used
    
    def get_style_dict(self):
        result = dict()
        style_name_list = set(self.__dict__.keys()) - {"style_name"}
        for param_name in style_name_list:
            result[param_name] = self.__dict__[param_name]
        return result


class PlotElement(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str
    data: PlotDataSupported = Field(discriminator="relation")
    style: PlotStyle

    # convert plot into axes-unlinked plot
    def compile(self):
        arguments = []

        # retrieve data-parameter
        param_data_dict = self.data.get_param_data_dict()
        for param_name in param_data_dict:
            data_name = param_data_dict[param_name]
            arguments.append(f"{param_name}=data_{data_name}")

        # retrieve style-parameter
        style_dict = self.style.get_style_dict()
        for style_name in style_dict:
            style_value = style_dict[style_name]
            arguments.append(f"{style_name}={style_value}")

        # combine into one line
        arguments_fragment = ", ".join(arguments)
        return f"{self.data.relation}({arguments_fragment})"


#################################################################
#   Data
#################################################################


class DataElement(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str
    value: List[float]


#################################################################
#   Request
#################################################################


class RequestElement(BaseModel):
    model_config = ConfigDict(extra="forbid")
    request_id: uuid.UUID
    figure: Figure
    axes: List[AxesElement]
    plot: List[PlotElement]
    data: List[DataElement]

    @classmethod
    def get_duplicate_list(cls, L: List[str]):
        return [item for (item, count) in collections.Counter(L).items() if (count > 1)]

    # Check if every (axes[].name, plot[].name, data[].name) unique
    @field_validator("axes", "plot", "data")
    @classmethod
    def check_uniqueness(cls, attr: List[Any], info: ValidationInfo) -> Any:
        attr_names = [at.name for at in attr]
        duplicative_attr_names = cls.get_duplicate_list(attr_names)

        if len(duplicative_attr_names) > 0:
            raise CodeReject(
                f"Duplicative {info.field_name} name found: {duplicative_attr_names}"
            )

        return attr

    # check if figure.axes[] has corresponding axes name
    @model_validator(mode="after")
    def check_figure_has_valid_axes(self):
        # get every existing axes name
        axes_names = [ax.name for ax in self.axes]

        for i, j in itertools.product(
            range(self.figure.size.row), range(self.figure.size.column)
        ):
            figure_axes = self.figure.axes[i][j]
            if (figure_axes is not None) and (figure_axes not in axes_names):
                raise CodeReject(
                    f"Cannot find figure.axes[{i}][{j}] = '{figure_axes}' in axes names"
                )

        return self

    # subfunction for self.check_axes_has_valid_plot
    def lookup_single_axes(self, axes_element: AxesElement, plot_names: List[str]):
        for plt in axes_element.plot:
            if plt not in plot_names:
                raise CodeReject(
                    f"Cannot find plot '{plt}' from axes {axes_element.name} in plot names"
                )

    # check if axes.plot[] has corresponding plot name
    @model_validator(mode="after")
    def check_axes_has_valid_plot(self):
        # get every existing plot name
        plot_names = [plt.name for plt in self.plot]

        for axes_element in self.axes:
            self.lookup_single_axes(axes_element, plot_names)

        return self

    # subfunction for self.check_plot_has_valid_data
    def lookup_single_plot(self, plot_element: PlotElement, data_names: List[str]):
        # get plot's using data name references
        using_data_names = set(plot_element.data.get_param_data_dict().values())

        # check if (using data names) is subset of (data names)
        if not using_data_names <= set(data_names):
            unknown_data = using_data_names - set(data_names)
            raise CodeReject(
                f"Cannot find data {unknown_data} from plot {plot_element.name} in data names"
            )

    # check if plot[].data.(!relation) has corresponding data name
    @model_validator(mode="after")
    def check_plot_has_valid_data(self):
        # get every existing data name
        data_names = [dt.name for dt in self.data]

        for plot_element in self.plot:
            self.lookup_single_plot(plot_element, data_names)

        return self
