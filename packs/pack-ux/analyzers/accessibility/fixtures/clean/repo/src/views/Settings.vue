<template>
  <div tabindex="0">
    <label for="lang">Język</label>
    <select id="lang" v-model="lang">
      <option value="pl">Polski</option>
    </select>
    <img :src="avatar" :alt="name">
    <textarea aria-label="Notatka" v-model="note"></textarea>
  </div>
</template>
