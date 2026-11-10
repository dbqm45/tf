<template>
  <p>{{ $t("profile.title") }}</p>
</template>

<script setup lang="ts">
const label = (a: number, b: number) => (a < b ? "mniej" : "więcej");
</script>

<route lang="yaml">
meta:
  layout: home
</route>
