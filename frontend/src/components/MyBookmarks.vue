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

// 获取收藏列表
async function loadBookmarks() {
    loading.value = true
    error.value = ''
    needLogin.value = false

    try {
        const response = await fetch('/api/bookmarks/')

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

// 取消收藏
async function removeBookmark(item) {
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
    <section class="discovery-page">
        <div class="discovery-heading">
            <div>
                <p class="discovery-eyebrow">MY COLLECTION</p>
                <h2>我的收藏</h2>
                <p>保存喜欢的澳门美食与特色文创。</p>
            </div>
        </div>

        <p v-if="loading" class="discovery-message">正在加载收藏...</p>

        <div v-else-if="needLogin" class="discovery-message">
            <p>登录后才能查看自己的收藏。</p>
            <a href="/accounts/login/?next=/">前往登录</a>
        </div>

        <p v-else-if="error" class="discovery-message error">
            {{ error }}
            <button @click="loadBookmarks">重试</button>
        </p>

        <div v-else-if="items.length" class="discovery-grid">
            <article v-for="item in items" :key="item.id" class="discovery-card">
                <div class="discovery-image">
                    <img v-if="item.image_url" :src="item.image_url" :alt="item.name" loading="lazy">
                    <div v-else class="image-placeholder">澳门漫遊</div>

                    <span class="discovery-area">{{ item.area_label }}</span>
                </div>

                <div class="discovery-card-body">
                    <p class="discovery-label">{{ item.kind === 'food' ? '地道美食' : '文创手信' }}</p>
                    <h3>{{ item.name }}</h3>

                    <p class="discovery-summary">{{ item.summary }}</p>

                    <div class="discovery-meta">
                        <span>{{ item.rating != null ? `★ ${Number(item.rating).toFixed(1)}` : '暂无评价'}}</span>
                        <span v-if="item.price">{{ item.price }}</span>
                    </div>

                    <button class="bookmark-remove-button" :disabled="removingId === item.id" @click="removeBookmark(item)">
                        {{ removingId === item.id ? '处理中...' : '取消收藏' }}
                    </button>
                </div>
            </article>
        </div>

        <div v-else class="discovery-message"> 你还没有收藏任何内容，去探索澳门吧！</div>

    </section>
</template>
