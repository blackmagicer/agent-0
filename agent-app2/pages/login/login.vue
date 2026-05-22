<!-- login.vue -->
<template>
  <view class="login-page">
    <view class="bg-orb bg-orb-1"></view>
    <view class="bg-orb bg-orb-2"></view>

    <view class="auth-shell">
      <!-- 品牌区 -->
      <view class="auth-brand">
        <view class="brand-icon">
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="1.5"/>
            <path d="M8 12h8M12 8v8" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          </svg>
        </view>
        <text class="brand-name">Agent</text>
        <text class="brand-tagline">智能对话助手</text>
      </view>

      <!-- 认证卡片 -->
      <view class="auth-card">
        <text class="auth-title">登录账号</text>
        <text class="auth-sub">欢迎回来，请输入您的账号信息</text>

        <view class="input-group">
          <text class="field-label">邮箱</text>
          <view class="input-wrap">
            <input
              v-model="form.email"
              class="field-input"
              type="text"
              placeholder="请输入注册邮箱"
              placeholder-class="ph"
              maxlength="50"
            />
          </view>
        </view>

        <view class="input-group">
          <text class="field-label">密码</text>
          <view class="input-wrap">
            <input
              v-model="form.password"
              class="field-input"
              type="password"
              placeholder="请输入密码"
              placeholder-class="ph"
              maxlength="20"
            />
          </view>
        </view>

        <button class="btn-primary" :class="{ loading: loading }" @click="onLogin" :disabled="loading">
          <text v-if="loading" class="btn-loading-dot"></text>
          <text v-else>登录</text>
        </button>

        <view class="auth-switch">
          <text class="switch-text">还没有账号？</text>
          <text class="switch-link" @click="onGotoRegister">立即注册</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, reactive } from 'vue'
import http from "/http/http.js"

const form = reactive({
  email: '',
  password: ''
})

const loading = ref(false)

const onLogin = async () => {
  if (!form.email.trim()) {
    uni.showToast({ title: '请输入邮箱', icon: 'none' })
    return
  }
  if (!form.password.trim()) {
    uni.showToast({ title: '请输入密码', icon: 'none' })
    return
  }

  const emailReg = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  if (!emailReg.test(form.email)) {
    uni.showToast({ title: '邮箱格式不正确', icon: 'none' })
    return
  }

  loading.value = true
  uni.showLoading({ title: '登录中...' })

  try {
    let result = await http.login(form.email, form.password);
    uni.showToast({ title: '登录成功', icon: 'success' });
    let user = result.user;
    let token = result.token;
    uni.setStorageSync("user", user);
    uni.setStorageSync("token", token);
    uni.redirectTo({ url: "/pages/index/index" })
  } catch (e) {
    uni.showToast({ title: e.message, icon: 'none' })
  } finally {
    loading.value = false;
    uni.hideLoading()
  }
}

const onGotoRegister = () => {
  uni.navigateTo({ url: '/pages/register/register' })
}
</script>

<style scoped>
page {
  background: #f0f2f7;
}

.login-page {
  min-height: 100vh;
  position: relative;
  overflow: hidden;
}

/* 背景光晕 */
.bg-orb {
  position: fixed;
  border-radius: 50%;
  filter: blur(80rpx);
  opacity: 0.18;
  pointer-events: none;
  z-index: 0;
}

.bg-orb-1 {
  width: 500rpx;
  height: 500rpx;
  background: #3b82f6;
  top: -120rpx;
  right: -100rpx;
}

.bg-orb-2 {
  width: 400rpx;
  height: 400rpx;
  background: #6366f1;
  bottom: -80rpx;
  left: -80rpx;
}

/* 主容器 */
.auth-shell {
  position: relative;
  z-index: 1;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60rpx 40rpx 40rpx;
  box-sizing: border-box;
}

/* 品牌区 */
.auth-brand {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 56rpx;
}

.brand-icon {
  width: 80rpx;
  height: 80rpx;
  color: #3b82f6;
  margin-bottom: 16rpx;
}

.brand-icon svg {
  width: 100%;
  height: 100%;
}

.brand-name {
  font-size: 44rpx;
  font-weight: 700;
  color: #111827;
  letter-spacing: 1rpx;
  margin-bottom: 8rpx;
}

.brand-tagline {
  font-size: 26rpx;
  color: #6b7280;
}

/* 认证卡片 */
.auth-card {
  width: 100%;
  max-width: 680rpx;
  background: #ffffff;
  border-radius: 32rpx;
  box-shadow: 0 8rpx 40rpx rgba(0, 0, 0, 0.06), 0 2rpx 12rpx rgba(59, 130, 246, 0.04);
  padding: 52rpx 52rpx 48rpx;
  box-sizing: border-box;
}

.auth-title {
  display: block;
  font-size: 40rpx;
  font-weight: 700;
  color: #111827;
  margin-bottom: 10rpx;
}

.auth-sub {
  display: block;
  font-size: 26rpx;
  color: #8b95a7;
  margin-bottom: 44rpx;
  line-height: 1.5;
}

/* 输入组 */
.input-group {
  margin-bottom: 32rpx;
}

.field-label {
  display: block;
  font-size: 26rpx;
  color: #374151;
  font-weight: 500;
  margin-bottom: 14rpx;
}

.input-wrap {
  position: relative;
  width: 100%;
}

.field-input {
  width: 100%;
  height: 88rpx;
  padding: 0 28rpx;
  border-radius: 20rpx;
  background: #f8f9fb;
  border: 2rpx solid #e8ecf0;
  font-size: 30rpx;
  color: #111827;
  box-sizing: border-box;
  transition: border-color 0.2s, background 0.2s;
}

.field-input:focus {
  border-color: #3b82f6;
  background: #f0f5ff;
  outline: none;
}

.ph {
  color: #adb5bd;
}

/* 主按钮 */
.btn-primary {
  width: 100%;
  height: 88rpx;
  border-radius: 20rpx;
  color: #ffffff;
  background: #3b82f6;
  border: none;
  font-size: 32rpx;
  font-weight: 600;
  letter-spacing: 2rpx;
  margin-top: 12rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 6rpx 24rpx rgba(59, 130, 246, 0.28);
  transition: background 0.2s, opacity 0.2s, transform 0.15s;
}

.btn-primary:active {
  transform: scale(0.98);
  background: #2563eb;
}

.btn-primary[disabled] {
  opacity: 0.65;
  pointer-events: none;
}

.btn-primary.loading {
  background: #93c5fd;
  box-shadow: none;
}

.btn-loading-dot {
  width: 20rpx;
  height: 20rpx;
  border-radius: 50%;
  background: #fff;
  animation: btn-pulse 0.8s ease-in-out infinite;
}

@keyframes btn-pulse {
  0%, 100% { opacity: 0.5; transform: scale(0.8); }
  50% { opacity: 1; transform: scale(1); }
}

/* 底部跳转 */
.auth-switch {
  display: flex;
  justify-content: center;
  align-items: center;
  margin-top: 36rpx;
  font-size: 26rpx;
}

.switch-text {
  color: #8b95a7;
}

.switch-link {
  color: #3b82f6;
  font-weight: 600;
  margin-left: 8rpx;
}
</style>