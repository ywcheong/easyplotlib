<script setup lang="ts">
import { FloatLabel, InputText, Button } from 'primevue';
import { usePyRequestBuilder } from '@/stores/requestbuild';

const builder = usePyRequestBuilder();
</script>

<template>
    <div class="w-full">
        <!-- Add New Data Button -->
        <Button label="New Data" icon="pi pi-plus" class="p-button-success mb-4" size="small"
            @click="builder.addEmptyData" />

        <div v-for="(dataElement, dataIndex) in builder.getDataList" :key="dataIndex">
            <div class="flex mt-3">
                <!-- Data Name Input -->
                <FloatLabel variant="on" :id="`data-name-${dataIndex}`" class="ml-4 flex-initial">
                    <InputText v-model="dataElement.name" @blur="builder.checkDataName(dataElement)"
                        v-tooltip.bottom="'Unique data name.'" size="small"
                        :invalid="dataElement.name.length === 0" />
                    <label :for="`data-name-${dataIndex}`" class="p-d-block">Data Name {{ dataElement.name }}</label>
                </FloatLabel>

                <!-- Data Value Input -->
                <FloatLabel variant="on" :id="`data-value-${dataIndex}`" class="ml-4 flex-auto">
                    <InputText v-model="dataElement.value" @blur="builder.checkDataValue(dataElement)"
                        v-tooltip.bottom="'Only accepts comma-seperated int/float(mix allowed).'" size="small"
                        class="w-full" :invalid="dataElement.value.length === 0" />
                    <label :for="`data-value-${dataIndex}`" class="p-d-block">Data Value (shape = ({{
                        dataElement.valueShape.join(", ") }}))</label>
                </FloatLabel>

                <!-- Delete Button -->
                <Button icon="pi pi-trash" @click="builder.removeData(dataIndex)"
                    class="p-button-danger ml-4 mr-4 flex-initial" />
            </div>
        </div>
    </div>
</template>