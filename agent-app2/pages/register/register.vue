<!-- register.vue -->
<template>
  <view class="register-page">
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
        <text class="auth-title">创建账号</text>
        <text class="auth-sub">注册后即可进入你的 AI 对话工作台</text>

        <view class="input-group">
          <text class="field-label">用户名</text>
          <view class="input-wrap">
            <input
              v-model="form.username"
              class="field-input"
              type="text"
              placeholder="2-12位字母/数字/中文"
              placeholder-class="ph"
              maxlength="12"
            />
          </view>
        </view>

        <view class="input-group">
          <text class="field-label">邮箱</text>
          <view class="input-wrap">
            <input
              v-model="form.email"
              class="field-input"
              type="text"
              placeholder="用于接收验证码"
              placeholder-class="ph"
              maxlength="50"
            />
          </view>
        </view>

        <view class="input-group">
          <text class="field-label">验证码</text>
          <view class="code-wrap">
            <input
              v-model="form.code"
              class="field-input code-input"
              type="number"
              placeholder="请输入4位验证码"
              placeholder-class="ph"
              maxlength="4"
            />
            <button
              class="code-btn"
              :class="{ disabled: countdown > 0 }"
              @click="onSendCode"
              :disabled="countdown > 0"
            >
              {{ countdown > 0 ? `${countdown}s 后重发` : '获取验证码' }}
            </button>
          </view>
        </view>

        <view class="input-group">
          <text class="field-label">密码</text>
          <view class="input-wrap">
            <input
              v-model="form.password"
              class="field-input"
              type="password"
              placeholder="6-20位，建议含字母+数字"
              placeholder-class="ph"
              maxlength="20"
            />
          </view>
        </view>

        <view class="input-group">
          <text class="field-label">确认密码</text>
          <view class="input-wrap">
            <input
              v-model="form.confirmPassword"
              class="field-input"
              type="password"
              placeholder="请再次输入密码"
              placeholder-class="ph"
              maxlength="20"
            />
          </view>
        </view>

        <button class="btn-primary" :class="{ loading: loading }" @click="onRegister" :disabled="loading">
          <text v-if="loading" class="btn-loading-dot"></text>
          <text v-else>注册</text>
        </button>

        <view class="auth-switch">
          <text class="switch-text">已有账号？</text>
          <text class="switch-link" @click="onGotoLogin">立即登录</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, reactive } from 'vue'
import http from "/http/http.js"

const form = reactive({
  username: '',
  email: '',
  code: '',
  password: '',
  confirmPassword: ''
})

const loading = ref(false)
const countdown = ref(0)

const onSendCode = async () => {
  if (!form.email.trim()) {
    uni.showToast({ title: '请输入邮箱', icon: 'none' })
    return
  }
  const emailReg = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  if (!emailReg.test(form.email)) {
    uni.showToast({ title: '邮箱格式不正确', icon: 'none' })
    return
  }

  try {
    let result = await http.getEmailCode(form.email)
    console.log("result: ", result);
    uni.showToast({ title: '验证码已发送', icon: 'success' })
    countdown.value = 60
    const timer = setInterval(() => {
      if (countdown.value > 0) {
        countdown.value--
      } else {
        clearInterval(timer)
      }
    }, 1000);
  } catch (e) {
    uni.showToast({ title: e.message, icon: 'none' })
  }
}

const onRegister = async () => {
  if (!form.username.trim()) {
    uni.showToast({ title: '请输入用户名', icon: 'none' })
    return
  }
  if (form.username.length < 2) {
    uni.showToast({ title: '用户名至少2位', icon: 'none' })
    return
  }
  if (!form.email.trim()) {
    uni.showToast({ title: '请输入邮箱', icon: 'none' })
    return
  }
  const emailReg = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  if (!emailReg.test(form.email)) {
    uni.showToast({ title: '邮箱格式不正确', icon: 'none' })
    return
  }
  if (!form.code.trim()) {
    uni.showToast({ title: '请输入验证码', icon: 'none' })
    return
  }
  if (form.code.length !== 4) {
    uni.showToast({ title: '验证码为4位数字', icon: 'none' })
    return
  }
  if (!form.password.trim()) {
    uni.showToast({ title: '请输入密码', icon: 'none' })
    return
  }
  if (form.password.length < 6) {
    uni.showToast({ title: '密码至少6位', icon: 'none' })
    return
  }
  if (form.password !== form.confirmPassword) {
    uni.showToast({ title: '两次密码不一致', icon: 'none' })
    return
  }

  loading.value = true
  uni.showLoading({ title: '注册中...' })

  try {
    let result = await http.register({
      "username": form.username,
      "email": form.email,
      "code": form.code,
      "password": form.password,
      "confirm_password": form.confirmPassword
    })
    console.log("register result: ", result)
    uni.showToast({ title: '注册成功！', icon: 'success' })
    uni.redirectTo({ url: '/pages/login/login' })
  } catch (e) {
    uni.showToast({ title: e.message, icon: 'none' })
  } finally {
    loading.value = false
    uni.hideLoading()
  }
}

const onGotoLogin = () => {
  uni.redirectTo({ url: '/pages/login/login' })
}
</script>

<style scoped>
page {
  background: #f0f2f7;
}

.register-page {
  min-height: 100vh;
  position: relative;
  overflow: hidden;
}

.bg-orb {
  position: fixed;
  border-radius: 50%;
  filter: blur(80rpx);
  opacity: 0.18;
  pointer-events: none;
  z-index: 0;
}

.bg-orb-1 {
  width: 520rpx;
  height: 520rpx;
  background: #3b82f6;
  top: -120rpx;
  right: -100rpx;
}

.bg-orb-2 {
  width: 420rpx;
  height: 420rpx;
  background: #6366f1;
  bottom: -100rpx;
  left: -80rpx;
}

.auth-shell {
  position: relative;
  z-index: 1;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 56rpx 40rpx 40rpx;
  box-sizing: border-box;
}

.auth-brand {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 48rpx;
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

.auth-card {
  width: 100%;
  max-width: 720rpx;
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
  margin-bottom: 40rpx;
  line-height: 1.5;
}

.input-group {
  margin-bottom: 28rpx;
}

.field-label {
  display: block;
  font-size: 26rpx;
  color: #374151;
  font-weight: 500;
  margin-bottom: 14rpx;
}

.input-wrap,
.code-wrap {
  position: relative;
  width: 100%;
  display: flex;
}

.field-input {
  flex: 1;
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

.code-input {
  border-top-right-radius: 0;
  border-bottom-right-radius: 0;
  border-right: none;
}

.code-btn {
  width: 210rpx;
  height: 88rpx;
  border-top-right-radius: 20rpx;
  border-bottom-right-radius: 20rpx;
  border-top-left-radius: 0;
  border-bottom-left-radius: 0;
  border: 2rpx solid #dbe5f4;
  border-left: none;
  background: #eff5ff;
  color: #3b82f6;
  font-size: 24rpx;
  font-weight: 600;
}

.code-btn:not(.disabled):active {
  background: #dbeafe;
}

.code-btn.disabled {
  opacity: 0.6;
  color: #94a3b8;
}

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
  margin-top: 16rpx;
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