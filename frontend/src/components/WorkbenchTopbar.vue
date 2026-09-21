<script setup lang="ts">
import type { IdentityResponse } from "@/types/api";

defineProps<{
  identity: IdentityResponse | null;
}>();
</script>

<template>
  <header class="topbar">
    <div class="brand">
      <span class="brand-name">Aily</span>
      <span class="brand-sub">企业智能助手</span>
    </div>
    <input class="search-disabled" disabled value="" placeholder="搜索对话、文档或功能" />
    <div class="identity">
      <div class="avatar">{{ identity?.display_name?.slice(0, 1) ?? "林" }}</div>
      <div>
        <div>{{ identity?.display_name ?? "林小北" }}</div>
        <div class="brand-sub">{{ identity?.department ?? "产品部" }}</div>
      </div>
    </div>
  </header>
</template>
