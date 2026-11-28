<script setup>
import { ref, onMounted } from 'vue'

// 收藏数据
const items = ref([])
const loading = ref(false)
const error = ref('')
const needLogin = ref(false)

// 正在取消收藏的内容
const removingId = ref(null)

// 获取 CSRF Token
function getCsrfToken() {
    const cookie = document.cookie.split('; ').find(item => item.startsWith('csrftoken='))
    return cookie ? decodeURIComponent(cookie.split('=')[1]) : ''
}

// 获取收藏列表  GET
async function loadBookmarks() {
    loading.value = true
    error.value = ''
    needLogin.value = false

    try {
        const response = await fetch('/api/bookmarks/', {
            method: 'GET'
        })

        if (response.status === 401) {
            needLogin.value = true
            return
        }
        if (!response.ok) {throw new Error(`HTTP ${response.status}`)}

        const data = await response.json()
        items.value = data.items || []
    } catch (err) {
        error.value = err.message || '获取收藏失败'
    } finally {
        loading.value = false
    }
}

// 取消收藏 DELETE
async function removeBookmark(item) {
    if (removingId.value !== null) return
    removingId.value = item.id
    error.value = ''

    try {
        const response = await fetch(`/api/listings/${item.id}/bookmark/`,
            {
                method: 'DELETE',
                headers: {'X-CSRFToken': getCsrfToken()}
            }
        )

        if (!response.ok) {throw new Error(`HTTP ${response.status}`)}

        // 从当前列表移除
        items.value = items.value.filter(place => place.id !== item.id)
    } catch (err) {
        error.value = err.message || '取消收藏失败'
    } finally {
        removingId.value = null
    }
}

// 页面初始化
onMounted(loadBookmarks)
</script>

<template>
    <section>
        <div class="section-heading">
            <div><p class="eyebrow">MY COLLECTION</p><h2>我的收藏</h2><p>保存喜欢的澳门美食与特色文创。</p></div>
        </div>
        <div v-loading="loading" element-loading-text="正在加载收藏..." class="loading-region">
            <el-empty v-if="needLogin" description="登录后才能查看自己的收藏。">
                <el-link href="/accounts/login/?next=/" type="primary">前往登录</el-link>
            </el-empty>
            <template v-else>
                <el-alert v-if="error" :title="error" type="error" :closable="false" show-icon>
                    <el-button @click="loadBookmarks">重试</el-button>
                </el-alert>
                <el-row v-if="items.length" :gutter="20" class="card-row">
                    <el-col v-for="item in items" :key="item.id" :xs="24" :sm="12" :lg="8">
                        <el-card shadow="hover" class="content-card">
                            <el-image :src="item.image_url || ''" :alt="item.name" fit="cover" loading="lazy" class="card-image">
                                <template #error><div class="image-placeholder">澳门漫遊</div></template>
                            </el-image>
                            <el-space wrap>
                                <el-tag>{{ item.kind === 'food' ? '地道美食' : '文创手信' }}</el-tag>
                                <el-tag type="info">{{ item.area_label }}</el-tag>
                            </el-space>
                            <h3>{{ item.name }}</h3>
                            <p class="summary">{{ item.summary }}</p>
                            <el-space wrap>
                                <el-text type="warning">{{ item.rating != null ? `★ ${Number(item.rating).toFixed(1)}` : '暂无评价' }}</el-text>
                                <el-text v-if="item.price" type="info">{{ item.price }}</el-text>
                            </el-space>
                            <div class="section-gap">
                                <el-button :loading="removingId === item.id" :disabled="removingId !== null" @click="removeBookmark(item)">取消收藏</el-button>
                            </div>
                        </el-card>
                    </el-col>
                </el-row>
                <el-empty v-else-if="!loading && !error" description="你还没有收藏任何内容，去探索澳门吧！" />
            </template>
        </div>
    </section>
</template>
