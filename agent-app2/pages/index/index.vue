<template>
  <view class="page-wrap">
    <view class="sidebar">
      <view class="sidebar-header">
        <view class="brand-row">
          <text class="brand-logo">Agent</text>
          <view class="brand-actions">
            <text class="brand-action">⋯</text>
          </view>
        </view>

        <view class="new-chat-btn" @click="resetChat">
          <text class="new-chat-icon">⊕</text>
          <text class="new-chat-text">开启新对话</text>
        </view>
      </view>

      <scroll-view scroll-y="true" class="history-list">
        <view
          v-for="group in groupedHistory"
          :key="group.label"
          class="history-group"
        >
          <text class="history-group-title">{{ group.label }}</text>
          <view
            v-for="item in group.items"
            :key="item.id"
            class="history-item"
            :class="{ active: activeHistoryId === item.id }"
            @click="useHistory(item)"
          >
            <text class="history-title">{{ item.title }}</text>
          </view>
        </view>

        <view v-if="conversationList.length === 0" class="history-empty">
          暂无历史记录
        </view>
      </scroll-view>

      <view class="sidebar-footer">
        <view class="user-card">
          <view class="user-avatar">
            <text>{{ (userInfo.username || '格').slice(0, 1) }}</text>
          </view>
          <text class="user-name">{{ userInfo.username || '未登录用户' }}</text>
          <text class="user-more">⋯</text>
        </view>
      </view>
    </view>

    <view class="main">
      <scroll-view class="chat-area" :scroll-top="chatScrollTop" scroll-y="true">
        <view v-if="messages.length === 0" class="welcome-card">
          <text class="welcome-title">开始一个新的对话</text>
          <text class="welcome-text">输入你的问题，Agent 会为你生成清晰、专业、可继续追问的回复。</text>
        </view>

        <view v-else class="message-list">
          <view
            v-for="(item, index) in messages"
            :key="item.id || index"
            class="message-row"
            :class="item.role"
          >
            <view class="avatar" v-if="item.role !== 'user'">A</view>
            <view class="bubble">
              <text v-if="item.role !== 'user'" class="bubble-role">Agent</text>
              <view v-if="item.role === 'user' && item.uploaded_filename" class="file-attachment">
                <text class="file-icon">📄</text>
                <text class="file-name">{{ item.uploaded_filename }}</text>
              </view>
              <text class="bubble-content" selectable="true" user-select>{{ item.content }}</text>
              <view v-if="item.streaming" class="typing-indicator">
                <text class="dot"></text>
                <text class="dot"></text>
                <text class="dot"></text>
              </view>
            </view>
          </view>
          <view id="anchor-bottom"></view>
        </view>
      </scroll-view>

      <view class="composer">
        <view class="composer-shell">
          <view v-if="lastUploadedFilename" class="pending-file-card">
            <text class="pending-file-icon">📄</text>
            <text class="pending-file-name">{{ lastUploadedFilename }}</text>
          </view>
          <view class="composer-box">
            <view class="upload-btn" :class="{ disabled: loading || uploading }" @click="onChooseFile">
              <text class="upload-plus">+</text>
            </view>

            <textarea
              v-model="formData.query"
              class="composer-input"
              :class="{ expanded: isExpanded }"
              placeholder="有问题，尽管问"
              placeholder-class="placeholder"
              maxlength="1000"
              :show-count="false"
              :auto-height="true"
              @input="onInputChange"
              @keydown.enter.prevent="onSendQuery"
            />

            <view class="composer-actions">
              <view class="send-btn" :class="{ loading: loading, disabled: loading || uploading }" @click="onSendQuery">
                <svg class="send-icon" viewBox="0 0 24 24" fill="none">
                  <path d="M12 6V18" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"/>
                  <path d="M8.5 9.5V14.5" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"/>
                  <path d="M15.5 9.5V14.5" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"/>
                </svg>
              </view>
            </view>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, reactive, nextTick, computed, onMounted } from 'vue'
import http from "/http/http.js"

const userInfo = reactive(uni.getStorageSync('user') || {})
const formData = reactive({
  query: ''
})

const loading = ref(false)
const uploading = ref(false)
const messages = ref([])
const conversationList = ref([])
const isExpanded = ref(false)
const chatScrollTop = ref(0)
const activeHistoryId = ref(null)
const currentConversationId = ref(null)
const lastUploadedFilename = ref('')
const sessionFileId = ref('')
let msgIdCounter = 0

const groupedHistory = computed(() => {
  if (!conversationList.value.length) {
    return []
  }

  const groups = [
    { label: '7 天内', items: [] },
    { label: '30 天内', items: [] },
    { label: '更早', items: [] }
  ]
  const now = Date.now()
  const day = 24 * 60 * 60 * 1000

  conversationList.value.forEach((item) => {
    const createdAt = item.updated_at ? new Date(item.updated_at).getTime() : now
    const diffDays = Math.floor((now - createdAt) / day)
    if (diffDays < 7) {
      groups[0].items.push(item)
    } else if (diffDays < 30) {
      groups[1].items.push(item)
    } else {
      groups[2].items.push(item)
    }
  })

  return groups.filter(group => group.items.length > 0)
})

const scrollToBottom = () => {
  nextTick(() => {
    chatScrollTop.value += 999999
  })
}

const loadConversationList = async () => {
  const result = await http.listConversations()
  conversationList.value = result.items || []
}

const ensureConversation = async () => {
  if (currentConversationId.value) {
    return currentConversationId.value
  }
  const result = await http.createConversation()
  currentConversationId.value = result.id
  activeHistoryId.value = result.id
  await loadConversationList()
  return result.id
}

const resetChat = () => {
  formData.query = ''
  isExpanded.value = false
  messages.value = []
  activeHistoryId.value = null
  currentConversationId.value = null
  lastUploadedFilename.value = ''
  sessionFileId.value = ''
}

const useHistory = async (item) => {
  activeHistoryId.value = item.id
  currentConversationId.value = item.id
  formData.query = ''
  isExpanded.value = false
  lastUploadedFilename.value = ''
  sessionFileId.value = ''
  const list = await http.getMessages(item.id)
  messages.value = list.map(msg => ({
    id: msg.id,
    role: msg.role,
    content: msg.content,
    uploaded_filename: msg.uploaded_filename,
    session_file_id: msg.session_file_id,
    created_at: msg.created_at
  }))
  scrollToBottom()
}

const onInputChange = (e) => {
  formData.query = e.detail.value
  isExpanded.value = formData.query.trim().length > 0
}

const onChooseFile = () => {
  if (loading.value || uploading.value) return

  uni.chooseFile({
    count: 1,
    extension: ['.txt', '.pdf'],
    success: async (res) => {
      const file = res.tempFiles?.[0]
      const filePath = file?.path || file?.tempFilePath
      const fileName = file?.name || (filePath ? filePath.split('/').pop() : '')
      if (!filePath || !fileName) {
        uni.showToast({ title: '未获取到文件', icon: 'none' })
        return
      }

      uploading.value = true
      try {
        const conversationId = await ensureConversation()
        const result = await http.uploadAgentFile(filePath, 'file', conversationId)
        uni.showToast({ title: '上传成功', icon: 'success' })
        lastUploadedFilename.value = result.filename || fileName
        sessionFileId.value = result.session_file_id || ''
        await loadConversationList()
      } catch (error) {
        uni.showToast({
          title: error?.message || '上传失败',
          icon: 'none'
        })
      } finally {
        uploading.value = false
      }
    },
    fail: (error) => {
      if (error?.errMsg && !error.errMsg.includes('cancel')) {
        uni.showToast({ title: '选择文件失败', icon: 'none' })
      }
    }
  })
}

const onSendQuery = async () => {
  if (!formData.query.trim()) {
    uni.showToast({ title: '请输入对话内容', icon: 'none' })
    return
  }
  if (loading.value || uploading.value) return

  const userQuery = formData.query.trim()
  const conversationId = await ensureConversation()
  formData.query = ''
  isExpanded.value = false
  loading.value = true

  messages.value.push({
    role: 'user',
    content: userQuery,
    uploaded_filename: lastUploadedFilename.value || null,
    session_file_id: sessionFileId.value || null
  })
  lastUploadedFilename.value = ''
  sessionFileId.value = ''
  activeHistoryId.value = conversationId
  currentConversationId.value = conversationId
  scrollToBottom()

  const placeholderId = `msg-${++msgIdCounter}`
  messages.value.push({
    id: placeholderId,
    role: 'agent',
    content: '',
    streaming: true
  })
  scrollToBottom()

  let fullAnswer = ''

  try {
    await http.agentChatStream(userQuery, {
      onChunk: (chunk) => {
        fullAnswer += chunk
        const lastMsg = messages.value[messages.value.length - 1]
        if (lastMsg && lastMsg.streaming) {
          lastMsg.content += chunk
          scrollToBottom()
        }
      },
      onComplete: async (finalText) => {
        const lastMsg = messages.value[messages.value.length - 1]
        const answer = finalText || fullAnswer
        if (lastMsg && lastMsg.streaming) {
          lastMsg.content = answer
          lastMsg.streaming = false
        }
        if (messages.value.filter(item => item.role === 'user').length === 1) {
          await http.updateConversationTitle(conversationId, userQuery.slice(0, 50))
        }
        await loadConversationList()
        activeHistoryId.value = conversationId
        currentConversationId.value = conversationId
        scrollToBottom()
      },
      onError: (error) => {
        const lastMsg = messages.value[messages.value.length - 1]
        if (lastMsg && lastMsg.streaming) {
          lastMsg.content = '请求出错：' + (error?.message || '未知错误')
          lastMsg.streaming = false
        }
        scrollToBottom()
        uni.showToast({
          title: error?.message || '请求失败',
          icon: 'none'
        })
      }
    }, conversationId)
  } catch (error) {
    const lastMsg = messages.value[messages.value.length - 1]
    if (lastMsg && lastMsg.streaming) {
      lastMsg.content = '请求出错：' + (error?.message || '未知错误')
      lastMsg.streaming = false
    }
    scrollToBottom()
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadConversationList()
})
</script>

<style scoped>
page {
  height: 100vh;
  overflow: hidden;
  background: #f5f6f8;
}

.page-wrap {
  height: 100vh;
  display: flex;
  overflow: hidden;
  background: #f5f6f8;
}

.sidebar {
  width: 320rpx;
  height: 100vh;
  flex-shrink: 0;
  background: #f3f4f6;
  color: #111827;
  display: flex;
  flex-direction: column;
  padding: 18rpx 12rpx 16rpx;
  box-sizing: border-box;
  border-right: 1rpx solid #eceef3;
  overflow: hidden;
}

.sidebar-header {
  padding: 6rpx 2rpx 0;
}

.brand-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 18rpx;
  padding: 0 8rpx;
}

.brand-logo {
  font-size: 40rpx;
  font-weight: 700;
  color: #3b82f6;
  letter-spacing: -1rpx;
}

.brand-actions {
  display: flex;
  align-items: center;
  gap: 18rpx;
}

.brand-action {
  font-size: 30rpx;
  color: #6b7280;
}

.new-chat-btn {
  height: 76rpx;
  border-radius: 999rpx;
  background: #ffffff;
  border: 1rpx solid #e5e7eb;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10rpx;
  box-shadow: 0 2rpx 10rpx rgba(15, 23, 42, 0.03);
}

.new-chat-icon {
  font-size: 28rpx;
  color: #111827;
}

.new-chat-text {
  font-size: 28rpx;
  color: #111827;
  font-weight: 500;
}

.history-list {
  flex: 1;
  min-height: 0;
  margin-top: 22rpx;
  padding: 0 4rpx;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
}

.history-group {
  margin-bottom: 18rpx;
}

.history-group-title {
  display: block;
  padding: 0 10rpx 10rpx;
  font-size: 22rpx;
  color: #8b95a7;
  font-weight: 500;
}

.history-item {
  height: 68rpx;
  padding: 0 14rpx;
  border-radius: 18rpx;
  display: flex;
  align-items: center;
  margin-bottom: 8rpx;
}

.history-item.active {
  background: #dfe9ff;
}

.history-title {
  display: block;
  font-size: 26rpx;
  color: #111827;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.history-empty {
  font-size: 24rpx;
  color: #9ca3af;
  padding: 12rpx 10rpx;
}

.sidebar-footer {
  padding: 8rpx 4rpx 0;
}

.user-card {
  height: 74rpx;
  border-radius: 18rpx;
  display: flex;
  align-items: center;
  padding: 0 10rpx;
  background: #f3f4f6;
}

.user-avatar {
  width: 48rpx;
  height: 48rpx;
  border-radius: 50%;
  background: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #6b7280;
  font-size: 22rpx;
  margin-right: 10rpx;
}

.user-name {
  flex: 1;
  font-size: 24rpx;
  color: #374151;
}

.user-more {
  font-size: 28rpx;
  color: #6b7280;
}

.main {
  flex: 1;
  height: 100vh;
  display: flex;
  flex-direction: column;
  min-width: 0;
  background: #fafafa;
  overflow: hidden;
}

.chat-area {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 32rpx 14rpx 170rpx;
  box-sizing: border-box;
  -webkit-overflow-scrolling: touch;
}

.welcome-card {
  max-width: 860rpx;
  margin: 32rpx auto 0;
  text-align: center;
  padding: 32rpx 0;
}

.welcome-title {
  display: block;
  font-size: 42rpx;
  font-weight: 700;
  color: #111827;
  margin-bottom: 14rpx;
}

.welcome-text {
  display: block;
  font-size: 26rpx;
  color: #6b7280;
  line-height: 1.6;
}


.message-list {
  max-width: 100%;
  margin: 0;
}

.message-row {
  display: flex;
  gap: 12rpx;
  margin-bottom: 12rpx;
  align-items: flex-start;
  width: 100%;
}

.message-row.user {
  flex-direction: row-reverse;
}

.avatar {
  width: 36rpx;
  height: 36rpx;
  line-height: 36rpx;
  text-align: center;
  border-radius: 50%;
  background: #dbeafe;
  color: #1d4ed8;
  font-size: 20rpx;
  font-weight: 700;
  flex-shrink: 0;
  margin-top: 3rpx;
}

.message-row.agent .avatar {
  background: #111827;
  color: #fff;
}

.bubble {
  display: inline-block;
  width: fit-content;
  max-width: 97%;
  padding: 10rpx 14rpx;
  border-radius: 18rpx;
  background: #ffffff;
  border: 1rpx solid #e7eaf0;
  box-sizing: border-box;
}

.message-row.user .bubble {
  margin-left: auto;
  text-align: right;
  background: #eef4ff;
  border-color: #d9e4ff;
}

.message-row.agent .bubble {
  margin-right: auto;
  margin-left: 0;
  text-align: left;
  width: auto;
}

.bubble-role {
  display: block;
  font-size: 22rpx;
  color: #6b7280;
  margin-bottom: 4rpx;
}

.bubble-content {
  display: block;
  font-size: 28rpx;
  color: #111827;
  line-height: 1.7;
  white-space: pre-wrap;
}

.pending-file-card {
  display: flex;
  align-items: center;
  gap: 8rpx;
  margin: 0 0 12rpx;
  padding: 12rpx 16rpx;
  background: rgba(255, 255, 255, 0.96);
  border: 1rpx solid #dbe5f4;
  border-radius: 18rpx;
  box-shadow: 0 2rpx 8rpx rgba(15, 23, 42, 0.05);
}

.pending-file-icon {
  font-size: 28rpx;
  flex-shrink: 0;
}

.pending-file-name {
  flex: 1;
  min-width: 0;
  font-size: 24rpx;
  color: #374151;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.file-attachment {
  display: flex;
  align-items: center;
  gap: 8rpx;
  margin-top: 10rpx;
  padding: 10rpx 16rpx;
  background: #eff6ff;
  border-radius: 12rpx;
  border: 1rpx solid #bfdbfe;
}

.file-icon {
  font-size: 28rpx;
  flex-shrink: 0;
}

.file-name {
  font-size: 24rpx;
  color: #1d4ed8;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.composer {
  position: fixed;
  left: 320rpx;
  right: 0;
  bottom: 0;
  padding: 0 20rpx 18rpx;
  box-sizing: border-box;
  background: linear-gradient(180deg, rgba(250,250,250,0) 0%, rgba(250,250,250,0.82) 30%, rgba(250,250,250,1) 100%);
}

.composer-shell {
  max-width: 980rpx;
  margin: 0 auto;
}

.composer-box {
  min-height: 72rpx;
  background: #ffffff;
  border: 1rpx solid #d9dce3;
  border-radius: 999rpx;
  padding: 10rpx 14rpx 10rpx 18rpx;
  box-shadow: 0 2rpx 8rpx rgba(15, 23, 42, 0.06);
  box-sizing: border-box;
  display: flex;
  align-items: center;
  gap: 14rpx;
}

.composer-input {
  flex: 1;
  width: 100%;
  min-height: 32rpx;
  max-height: 180rpx;
  padding: 6rpx 0;
  font-size: 28rpx;
  line-height: 1.35;
  color: #111827;
  box-sizing: border-box;
}

.composer-input.expanded {
  min-height: 32rpx;
}

.placeholder {
  color: #8b8f97;
}

.composer-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  margin-top: 0;
  flex-shrink: 0;
}

.upload-btn {
  width: 56rpx;
  height: 56rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.upload-plus {
  font-size: 42rpx;
  line-height: 1;
  font-weight: 300;
  color: #111827;
}

.send-btn {
  width: 56rpx;
  height: 56rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: #000000;
  color: #ffffff;
  flex-shrink: 0;
  transition: transform 0.2s ease, opacity 0.2s ease;
}

.send-icon {
  width: 26rpx;
  height: 26rpx;
}

.send-btn.loading {
  opacity: 0.8;
  animation: send-pulse 1.1s ease-in-out infinite;
}

.send-btn.disabled,
.upload-btn.disabled {
  pointer-events: none;
  opacity: 0.65;
}

.typing-indicator {
  display: inline-flex;
  align-items: center;
  gap: 6rpx;
  margin-top: 8rpx;
  padding: 6rpx 0;
}

.typing-indicator .dot {
  width: 8rpx;
  height: 8rpx;
  border-radius: 50%;
  background: #6ea8ff;
  animation: typing-bounce 1.4s ease-in-out infinite;
}

.typing-indicator .dot:nth-child(1) {
  animation-delay: 0s;
}

.typing-indicator .dot:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-indicator .dot:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes send-pulse {
  0%, 100% {
    transform: scale(1);
    opacity: 0.75;
  }
  50% {
    transform: scale(0.9);
    opacity: 1;
  }
}

@keyframes typing-bounce {
  0%, 60%, 100% {
    transform: translateY(0);
    opacity: 0.5;
  }
  30% {
    transform: translateY(-8rpx);
    opacity: 1;
  }
}
</style>
