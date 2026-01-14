<template>
  <div class="profile-page" :class="{ 'theme-dark': isDarkTheme }">
    <div class="page-header">
      <h2 class="page-title">
        <a-icon type="user" />
        <span>{{ $t('profile.title') || 'My Profile' }}</span>
      </h2>
      <p class="page-desc">{{ $t('profile.description') || 'Manage your account settings and preferences' }}</p>
    </div>

    <a-row :gutter="24" class="profile-cards-row">
      <!-- Left Column: Profile Card -->
      <a-col :xs="24" :md="8" class="profile-card-col">
        <a-card :bordered="false" class="profile-card">
          <div class="avatar-section">
            <a-avatar :size="100" :src="profile.avatar || '/avatar2.jpg'" />
            <h3 class="username">{{ profile.nickname || profile.username }}</h3>
            <p class="user-role">
              <a-tag :color="getRoleColor(profile.role)">
                {{ getRoleLabel(profile.role) }}
              </a-tag>
              <a-tag v-if="isVip" color="gold">
                <a-icon type="crown" />
                VIP
              </a-tag>
            </p>
          </div>
          <a-divider />
          <div class="profile-info">
            <div class="info-item">
              <a-icon type="user" />
              <span class="label">{{ $t('profile.username') || 'Username' }}:</span>
              <span class="value">{{ profile.username }}</span>
            </div>
            <div class="info-item">
              <a-icon type="mail" />
              <span class="label">{{ $t('profile.email') || 'Email' }}:</span>
              <span class="value">{{ profile.email || '-' }}</span>
            </div>
            <div class="info-item">
              <a-icon type="calendar" />
              <span class="label">{{ $t('profile.lastLogin') || 'Last Login' }}:</span>
              <span class="value">{{ formatTime(profile.last_login_at) || '-' }}</span>
            </div>
          </div>
        </a-card>
      </a-col>

      <!-- Right Column: Credits and Referral Cards -->
      <a-col :xs="24" :md="16" class="right-cards-col">
        <a-row :gutter="16" class="right-cards-row">
          <!-- Credits Card (积分卡片) -->
          <a-col :xs="24" :md="12">
            <a-card :bordered="false" class="credits-card">
              <div class="credits-header">
                <h3 class="credits-title">
                  <a-icon type="wallet" />
                  {{ $t('profile.credits.title') || '我的积分' }}
                </h3>
              </div>
              <div class="credits-body">
                <div class="credits-amount">
                  <span class="amount-value">{{ formatCredits(billing.credits) }}</span>
                  <span class="amount-label">{{ $t('profile.credits.unit') || '积分' }}</span>
                </div>
                <div class="vip-status" v-if="billing.vip_expires_at">
                  <a-icon type="crown" :style="{ color: isVip ? '#faad14' : '#999' }" />
                  <span v-if="isVip" class="vip-active">
                    {{ $t('profile.credits.vipExpires') || 'VIP有效期至' }}: {{ formatDate(billing.vip_expires_at) }}
                  </span>
                  <span v-else class="vip-expired">
                    {{ $t('profile.credits.vipExpired') || 'VIP已过期' }}
                  </span>
                </div>
                <div class="vip-status" v-else-if="!billing.is_vip">
                  <span class="no-vip">{{ $t('profile.credits.noVip') || '非VIP用户' }}</span>
                </div>
              </div>
              <a-divider />
              <div class="credits-actions">
                <a-button type="primary" icon="shopping" @click="handleRecharge">
                  {{ $t('profile.credits.recharge') || '开通/充值' }}
                </a-button>
              </div>
              <div class="credits-hint" v-if="billing.billing_enabled">
                <a-icon type="info-circle" />
                <span>{{ $t('profile.credits.hint') || '使用AI分析等功能会消耗积分，VIP用户免费' }}</span>
              </div>
            </a-card>
          </a-col>

          <!-- Referral Card (邀请卡片) -->
          <a-col :xs="24" :md="12">
            <a-card :bordered="false" class="referral-card">
              <div class="referral-header">
                <h3 class="referral-title">
                  <a-icon type="team" />
                  {{ $t('profile.referral.title') || '邀请好友' }}
                </h3>
              </div>
              <div class="referral-body">
                <div class="referral-stats">
                  <div class="stat-item">
                    <span class="stat-value">{{ referralData.total || 0 }}</span>
                    <span class="stat-label">{{ $t('profile.referral.totalInvited') || '已邀请' }}</span>
                  </div>
                  <div class="stat-item" v-if="referralData.referral_bonus > 0">
                    <span class="stat-value">+{{ referralData.referral_bonus }}</span>
                    <span class="stat-label">{{ $t('profile.referral.bonusPerInvite') || '每邀请获得' }}</span>
                  </div>
                </div>
                <a-divider style="margin: 12px 0" />
                <div class="referral-link-section">
                  <div class="link-label">{{ $t('profile.referral.yourLink') || '您的邀请链接' }}</div>
                  <div class="link-box">
                    <a-input
                      :value="referralLink"
                      readonly
                      size="small"
                    >
                      <a-tooltip slot="suffix" :title="$t('profile.referral.copyLink') || '复制链接'">
                        <a-icon type="copy" style="cursor: pointer" @click="copyReferralLink" />
                      </a-tooltip>
                    </a-input>
                  </div>
                </div>
                <div class="referral-hint" v-if="referralData.register_bonus > 0">
                  <a-icon type="gift" />
                  <span>{{ $t('profile.referral.newUserBonus') || '新用户注册获得' }} {{ referralData.register_bonus }} {{ $t('profile.credits.unit') || '积分' }}</span>
                </div>
              </div>
            </a-card>
          </a-col>
        </a-row>
      </a-col>
    </a-row>

    <!-- Edit Profile Tabs (Below Cards) -->
    <a-row :gutter="24" style="margin-top: 24px">
      <a-col :xs="24">
        <a-card :bordered="false" class="edit-card">
          <a-tabs v-model="activeTab">
            <!-- Basic Info Tab -->
            <a-tab-pane key="basic" :tab="$t('profile.basicInfo') || 'Basic Info'">
              <a-form :form="profileForm" layout="vertical" class="profile-form">
                <a-form-item :label="$t('profile.nickname') || 'Nickname'">
                  <a-input
                    v-decorator="['nickname', { initialValue: profile.nickname }]"
                    :placeholder="$t('profile.nicknamePlaceholder') || 'Enter your nickname'"
                  >
                    <a-icon slot="prefix" type="smile" />
                  </a-input>
                </a-form-item>

                <a-form-item :label="$t('profile.email') || 'Email'">
                  <a-input
                    :value="profile.email || '-'"
                    disabled
                  >
                    <a-icon slot="prefix" type="mail" />
                    <a-tooltip slot="suffix" :title="$t('profile.emailCannotChange') || 'Email cannot be changed after registration'">
                      <a-icon type="info-circle" style="color: rgba(0,0,0,.45)" />
                    </a-tooltip>
                  </a-input>
                </a-form-item>

                <a-form-item>
                  <a-button type="primary" :loading="saving" @click="handleSaveProfile">
                    <a-icon type="save" />
                    {{ $t('common.save') || 'Save' }}
                  </a-button>
                </a-form-item>
              </a-form>
            </a-tab-pane>

            <!-- Change Password Tab -->
            <a-tab-pane key="password" :tab="$t('profile.changePassword') || 'Change Password'">
              <a-form :form="passwordForm" layout="vertical" class="password-form">
                <a-alert
                  :message="$t('profile.passwordHintNew') || 'For security, email verification is required to change password. Password must be at least 8 characters with uppercase, lowercase, and number.'"
                  type="info"
                  showIcon
                  style="margin-bottom: 24px"
                />

                <!-- Email Display & Verification Code -->
                <a-form-item :label="$t('profile.verificationCode') || 'Verification Code'">
                  <a-row :gutter="12">
                    <a-col :span="16">
                      <a-input
                        v-decorator="['code', {
                          rules: [{ required: true, message: $t('profile.codeRequired') || 'Please enter verification code' }]
                        }]"
                        :placeholder="$t('profile.codePlaceholder') || 'Enter verification code'"
                      >
                        <a-icon slot="prefix" type="safety-certificate" />
                      </a-input>
                    </a-col>
                    <a-col :span="8">
                      <a-button
                        block
                        :loading="sendingPwdCode"
                        :disabled="sendingPwdCode || pwdCodeCountdown > 0 || !profile.email"
                        @click="handleSendPwdCode"
                      >
                        {{ pwdCodeCountdown > 0 ? `${pwdCodeCountdown}s` : ($t('profile.sendCode') || 'Send Code') }}
                      </a-button>
                    </a-col>
                  </a-row>
                  <div class="email-hint" v-if="profile.email">
                    {{ $t('profile.codeWillSendTo') || 'Code will be sent to' }}: {{ profile.email }}
                  </div>
                  <div class="email-hint email-warning" v-else>
                    {{ $t('profile.noEmailWarning') || 'Please set your email first in Basic Info tab' }}
                  </div>
                </a-form-item>

                <a-form-item :label="$t('profile.newPassword') || 'New Password'">
                  <a-input-password
                    v-decorator="['new_password', {
                      rules: [
                        { required: true, message: $t('profile.newPasswordRequired') || 'Please enter new password' },
                        { validator: validateNewPassword }
                      ]
                    }]"
                    :placeholder="$t('profile.newPasswordPlaceholder') || 'Enter new password'"
                  >
                    <a-icon slot="prefix" type="lock" />
                  </a-input-password>
                </a-form-item>

                <a-form-item :label="$t('profile.confirmPassword') || 'Confirm Password'">
                  <a-input-password
                    v-decorator="['confirm_password', {
                      rules: [
                        { required: true, message: $t('profile.confirmPasswordRequired') || 'Please confirm password' },
                        { validator: validateConfirmPassword }
                      ]
                    }]"
                    :placeholder="$t('profile.confirmPasswordPlaceholder') || 'Confirm new password'"
                  >
                    <a-icon slot="prefix" type="lock" />
                  </a-input-password>
                </a-form-item>

                <a-form-item>
                  <a-button type="primary" :loading="changingPassword" @click="handleChangePassword" :disabled="!profile.email">
                    <a-icon type="key" />
                    {{ $t('profile.changePassword') || 'Change Password' }}
                  </a-button>
                </a-form-item>
              </a-form>
            </a-tab-pane>

            <!-- Credits Log Tab (消费记录) -->
            <a-tab-pane key="credits" :tab="$t('profile.creditsLog') || '消费记录'">
              <a-table
                :columns="creditsLogColumns"
                :dataSource="creditsLog"
                :loading="creditsLogLoading"
                :pagination="creditsLogPagination"
                :rowKey="record => record.id"
                size="small"
                @change="handleCreditsLogChange"
              >
                <!-- Action Column -->
                <template slot="action" slot-scope="text">
                  <a-tag :color="getActionColor(text)">
                    {{ getActionLabel(text) }}
                  </a-tag>
                </template>

                <!-- Amount Column -->
                <template slot="amount" slot-scope="text">
                  <span :class="text >= 0 ? 'amount-positive' : 'amount-negative'">
                    {{ text >= 0 ? '+' : '' }}{{ text }}
                  </span>
                </template>

                <!-- Time Column -->
                <template slot="created_at" slot-scope="text">
                  {{ formatTime(text) }}
                </template>
              </a-table>
            </a-tab-pane>

            <!-- Referral List Tab (邀请列表) -->
            <a-tab-pane key="referrals" :tab="$t('profile.referral.listTab') || '邀请列表'">
              <a-table
                :columns="referralColumns"
                :dataSource="referralData.list || []"
                :loading="referralLoading"
                :pagination="referralPagination"
                :rowKey="record => record.id"
                size="small"
                @change="handleReferralChange"
              >
                <!-- Avatar & Name Column -->
                <template slot="user" slot-scope="text, record">
                  <div class="referral-user-cell">
                    <a-avatar :size="32" :src="record.avatar || '/avatar2.jpg'" />
                    <div class="user-info">
                      <span class="nickname">{{ record.nickname || record.username }}</span>
                      <span class="username">@{{ record.username }}</span>
                    </div>
                  </div>
                </template>

                <!-- Time Column -->
                <template slot="created_at" slot-scope="text">
                  {{ formatTime(text) }}
                </template>
              </a-table>

              <a-empty v-if="!referralLoading && (!referralData.list || referralData.list.length === 0)">
                <span slot="description">{{ $t('profile.referral.noReferrals') || '暂无邀请记录' }}</span>
                <a-button type="primary" @click="copyReferralLink">
                  {{ $t('profile.referral.shareNow') || '立即分享邀请' }}
                </a-button>
              </a-empty>
            </a-tab-pane>
          </a-tabs>
        </a-card>
      </a-col>
    </a-row>
  </div>
</template>

<script>
import { getProfile, updateProfile, getMyCreditsLog, getMyReferrals } from '@/api/user'
import { getSettingsValues } from '@/api/settings'
import { baseMixin } from '@/store/app-mixin'

export default {
  name: 'Profile',
  mixins: [baseMixin],
  data () {
    return {
      loading: false,
      saving: false,
      changingPassword: false,
      sendingPwdCode: false,
      pwdCodeCountdown: 0,
      pwdCodeTimer: null,
      activeTab: 'basic',
      profile: {
        id: null,
        username: '',
        nickname: '',
        email: '',
        avatar: '',
        role: 'user',
        last_login_at: null
      },
      // Credits log
      creditsLog: [],
      creditsLogLoading: false,
      creditsLogPagination: {
        current: 1,
        pageSize: 10,
        total: 0
      },
      // Referral data
      referralData: {
        list: [],
        total: 0,
        referral_code: '',
        referral_bonus: 0,
        register_bonus: 0
      },
      referralLoading: false,
      referralPagination: {
        current: 1,
        pageSize: 10,
        total: 0
      },
      billing: {
        credits: 0,
        is_vip: false,
        vip_expires_at: null,
        billing_enabled: false,
        vip_bypass: true,
        feature_costs: {},
        recharge_telegram_url: ''
      },
      rechargeTelegramUrl: 'https://t.me/your_support_bot'
    }
  },
  computed: {
    isDarkTheme () {
      return this.navTheme === 'dark' || this.navTheme === 'realdark'
    },
    isVip () {
      if (!this.billing.vip_expires_at) return false
      const expiresAt = new Date(this.billing.vip_expires_at)
      return expiresAt > new Date()
    },
    creditsLogColumns () {
      return [
        {
          title: this.$t('profile.creditsLog.time') || '时间',
          dataIndex: 'created_at',
          width: 160,
          scopedSlots: { customRender: 'created_at' }
        },
        {
          title: this.$t('profile.creditsLog.action') || '类型',
          dataIndex: 'action',
          width: 100,
          scopedSlots: { customRender: 'action' }
        },
        {
          title: this.$t('profile.creditsLog.amount') || '变动',
          dataIndex: 'amount',
          width: 100,
          scopedSlots: { customRender: 'amount' }
        },
        {
          title: this.$t('profile.creditsLog.balance') || '余额',
          dataIndex: 'balance_after',
          width: 100
        },
        {
          title: this.$t('profile.creditsLog.remark') || '备注',
          dataIndex: 'remark',
          ellipsis: true
        }
      ]
    },
    referralColumns () {
      return [
        {
          title: this.$t('profile.referral.user') || '用户',
          dataIndex: 'username',
          scopedSlots: { customRender: 'user' }
        },
        {
          title: this.$t('profile.referral.registerTime') || '注册时间',
          dataIndex: 'created_at',
          width: 180,
          scopedSlots: { customRender: 'created_at' }
        }
      ]
    },
    referralLink () {
      const baseUrl = window.location.origin + window.location.pathname
      const ref = this.referralData.referral_code || this.profile.id
      return `${baseUrl}#/user/login?ref=${ref}`
    }
  },
  watch: {
    activeTab (val) {
      if (val === 'credits' && this.creditsLog.length === 0) {
        this.loadCreditsLog()
      }
      if (val === 'referrals' && (!this.referralData.list || this.referralData.list.length === 0)) {
        this.loadReferrals()
      }
    }
  },
  beforeCreate () {
    this.profileForm = this.$form.createForm(this, { name: 'profile' })
    this.passwordForm = this.$form.createForm(this, { name: 'password' })
  },
  mounted () {
    this.loadProfile()
    this.loadReferrals()
  },
  beforeDestroy () {
    if (this.pwdCodeTimer) {
      clearInterval(this.pwdCodeTimer)
    }
  },
  methods: {
    async loadProfile () {
      this.loading = true
      try {
        const res = await getProfile()
        if (res.code === 1) {
          this.profile = res.data
          // 提取计费信息
          if (res.data.billing) {
            this.billing = res.data.billing
            // Prefer server-provided public recharge link
            if (this.billing.recharge_telegram_url) {
              this.rechargeTelegramUrl = this.billing.recharge_telegram_url
            }
          }
          this.$nextTick(() => {
            this.profileForm.setFieldsValue({
              nickname: this.profile.nickname,
              email: this.profile.email
            })
          })
        } else {
          this.$message.error(res.msg || 'Failed to load profile')
        }
      } catch (error) {
        this.$message.error('Failed to load profile')
      } finally {
        this.loading = false
      }
    },

    async loadRechargeUrl () {
      // 只有管理员才能获取设置，普通用户使用默认值
      if (this.profile.role === 'admin') {
        try {
          const res = await getSettingsValues()
          if (res.code === 1 && res.data && res.data.billing) {
            this.rechargeTelegramUrl = res.data.billing.RECHARGE_TELEGRAM_URL || this.rechargeTelegramUrl
          }
        } catch (e) {
          // 忽略错误，使用默认值
        }
      }
    },

    handleRecharge () {
      // 跳转到 Telegram 客服
      window.open(this.rechargeTelegramUrl, '_blank')
    },

    formatCredits (credits) {
      if (!credits && credits !== 0) return '0'
      return Number(credits).toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 2 })
    },

    formatDate (dateStr) {
      if (!dateStr) return ''
      const date = new Date(dateStr)
      return date.toLocaleDateString()
    },

    handleSaveProfile () {
      this.profileForm.validateFields(async (err, values) => {
        if (err) return

        this.saving = true
        try {
          const res = await updateProfile(values)
          if (res.code === 1) {
            this.$message.success(res.msg || 'Profile updated successfully')
            this.loadProfile()
          } else {
            this.$message.error(res.msg || 'Update failed')
          }
        } catch (error) {
          this.$message.error('Update failed')
        } finally {
          this.saving = false
        }
      })
    },

    validateConfirmPassword (rule, value, callback) {
      const newPassword = this.passwordForm.getFieldValue('new_password')
      if (value && value !== newPassword) {
        callback(this.$t('profile.passwordMismatch') || 'Passwords do not match')
      } else {
        callback()
      }
    },

    async handleSendPwdCode () {
      if (!this.profile.email) {
        this.$message.error(this.$t('profile.noEmailWarning') || 'Please set your email first')
        return
      }

      this.sendingPwdCode = true
      try {
        const { sendVerificationCode } = await import('@/api/auth')
        const res = await sendVerificationCode({
          email: this.profile.email,
          type: 'change_password'
        })
        if (res.code === 1) {
          this.$message.success(this.$t('profile.codeSent') || 'Verification code sent')
          this.startPwdCodeCountdown()
        } else {
          this.$message.error(res.msg || 'Failed to send code')
        }
      } catch (error) {
        this.$message.error(error.response?.data?.msg || 'Failed to send code')
      } finally {
        this.sendingPwdCode = false
      }
    },

    startPwdCodeCountdown () {
      this.pwdCodeCountdown = 60
      this.pwdCodeTimer = setInterval(() => {
        this.pwdCodeCountdown--
        if (this.pwdCodeCountdown <= 0) {
          clearInterval(this.pwdCodeTimer)
          this.pwdCodeTimer = null
        }
      }, 1000)
    },

    validateNewPassword (rule, value, callback) {
      if (!value) {
        callback()
        return
      }
      if (value.length < 8) {
        callback(new Error(this.$t('user.register.pwdMinLength') || 'At least 8 characters'))
        return
      }
      if (!/[A-Z]/.test(value)) {
        callback(new Error(this.$t('user.register.pwdUppercase') || 'At least one uppercase letter'))
        return
      }
      if (!/[a-z]/.test(value)) {
        callback(new Error(this.$t('user.register.pwdLowercase') || 'At least one lowercase letter'))
        return
      }
      if (!/[0-9]/.test(value)) {
        callback(new Error(this.$t('user.register.pwdNumber') || 'At least one number'))
        return
      }
      callback()
    },

    handleChangePassword () {
      this.passwordForm.validateFields(async (err, values) => {
        if (err) return

        this.changingPassword = true
        try {
          const { changePassword: changePasswordApi } = await import('@/api/auth')
          const res = await changePasswordApi({
            code: values.code,
            new_password: values.new_password
          })
          if (res.code === 1) {
            this.$message.success(res.msg || 'Password changed successfully')
            this.passwordForm.resetFields()
          } else {
            this.$message.error(res.msg || 'Change password failed')
          }
        } catch (error) {
          this.$message.error(error.response?.data?.msg || 'Change password failed')
        } finally {
          this.changingPassword = false
        }
      })
    },

    getRoleColor (role) {
      const colors = {
        admin: 'red',
        manager: 'orange',
        user: 'blue',
        viewer: 'default'
      }
      return colors[role] || 'default'
    },

    getRoleLabel (role) {
      const labels = {
        admin: this.$t('userManage.roleAdmin') || 'Admin',
        manager: this.$t('userManage.roleManager') || 'Manager',
        user: this.$t('userManage.roleUser') || 'User',
        viewer: this.$t('userManage.roleViewer') || 'Viewer'
      }
      return labels[role] || role
    },

    formatTime (timestamp) {
      if (!timestamp) return ''
      const date = new Date(typeof timestamp === 'number' ? timestamp * 1000 : timestamp)
      return date.toLocaleString()
    },

    // Credits log methods
    async loadCreditsLog () {
      this.creditsLogLoading = true
      try {
        const res = await getMyCreditsLog({
          page: this.creditsLogPagination.current,
          page_size: this.creditsLogPagination.pageSize
        })
        if (res.code === 1) {
          this.creditsLog = res.data.items || []
          this.creditsLogPagination.total = res.data.total || 0
        }
      } catch (e) {
        this.$message.error('Failed to load credits log')
      } finally {
        this.creditsLogLoading = false
      }
    },

    handleCreditsLogChange (pagination) {
      this.creditsLogPagination.current = pagination.current
      this.loadCreditsLog()
    },

    // Referral methods
    async loadReferrals () {
      this.referralLoading = true
      try {
        const res = await getMyReferrals({
          page: this.referralPagination.current,
          page_size: this.referralPagination.pageSize
        })
        if (res.code === 1) {
          this.referralData = {
            list: res.data.list || [],
            total: res.data.total || 0,
            referral_code: res.data.referral_code || '',
            referral_bonus: res.data.referral_bonus || 0,
            register_bonus: res.data.register_bonus || 0
          }
          this.referralPagination.total = res.data.total || 0
        }
      } catch (e) {
        this.$message.error('Failed to load referral data')
      } finally {
        this.referralLoading = false
      }
    },

    handleReferralChange (pagination) {
      this.referralPagination.current = pagination.current
      this.loadReferrals()
    },

    copyReferralLink () {
      const link = this.referralLink
      if (navigator.clipboard) {
        navigator.clipboard.writeText(link).then(() => {
          this.$message.success(this.$t('profile.referral.linkCopied') || '邀请链接已复制')
        }).catch(() => {
          this.fallbackCopy(link)
        })
      } else {
        this.fallbackCopy(link)
      }
    },

    fallbackCopy (text) {
      const textarea = document.createElement('textarea')
      textarea.value = text
      document.body.appendChild(textarea)
      textarea.select()
      try {
        document.execCommand('copy')
        this.$message.success(this.$t('profile.referral.linkCopied') || '邀请链接已复制')
      } catch (err) {
        this.$message.error('Copy failed')
      }
      document.body.removeChild(textarea)
    },

    getActionColor (action) {
      const colors = {
        consume: 'red',
        recharge: 'green',
        admin_adjust: 'blue',
        refund: 'orange',
        vip_grant: 'gold',
        vip_revoke: 'default',
        register_bonus: 'cyan',
        referral_bonus: 'purple'
      }
      return colors[action] || 'default'
    },

    getActionLabel (action) {
      const labels = {
        consume: this.$t('profile.creditsLog.actionConsume') || '消费',
        recharge: this.$t('profile.creditsLog.actionRecharge') || '充值',
        admin_adjust: this.$t('profile.creditsLog.actionAdjust') || '调整',
        refund: this.$t('profile.creditsLog.actionRefund') || '退款',
        vip_grant: this.$t('profile.creditsLog.actionVipGrant') || 'VIP授予',
        vip_revoke: this.$t('profile.creditsLog.actionVipRevoke') || 'VIP取消',
        register_bonus: this.$t('profile.creditsLog.actionRegisterBonus') || '注册奖励',
        referral_bonus: this.$t('profile.creditsLog.actionReferralBonus') || '邀请奖励'
      }
      return labels[action] || action
    }
  }
}
</script>

<style lang="less" scoped>
@primary-color: #1890ff;

.profile-page {
  padding: 24px;
  min-height: calc(100vh - 120px);
  background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);

  .page-header {
    margin-bottom: 24px;

    .page-title {
      font-size: 24px;
      font-weight: 700;
      margin: 0 0 8px 0;
      color: #1e3a5f;
      display: flex;
      align-items: center;
      gap: 12px;

      .anticon {
        font-size: 28px;
        color: @primary-color;
      }
    }

    .page-desc {
      color: #64748b;
      font-size: 14px;
      margin: 0;
    }
  }

  // Profile cards row - make cards same height
  .profile-cards-row {
    display: flex;
    align-items: stretch;

    .profile-card-col,
    .right-cards-col {
      display: flex;
      flex-direction: column;

      .ant-card {
        height: 100%;
        display: flex;
        flex-direction: column;
      }

      /deep/ .ant-card-body {
        flex: 1;
        display: flex;
        flex-direction: column;
      }
    }

    .right-cards-row {
      height: 100%;
      display: flex;

      .ant-col {
        display: flex;
        flex-direction: column;

        .ant-card {
          height: 100%;
          display: flex;
          flex-direction: column;
        }

        /deep/ .ant-card-body {
          flex: 1;
          display: flex;
          flex-direction: column;
        }
      }
    }
  }

  .profile-card {
    border-radius: 12px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
    text-align: center;

    .avatar-section {
      padding: 20px 0;

      .ant-avatar {
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
      }

      .username {
        margin: 16px 0 8px;
        font-size: 20px;
        font-weight: 600;
        color: #1e3a5f;
      }

      .user-role {
        margin: 0;
      }
    }

    .profile-info {
      text-align: left;
      flex: 1;
      display: flex;
      flex-direction: column;
      justify-content: space-around;

      .info-item {
        display: flex;
        align-items: center;
        padding: 12px 0;
        border-bottom: 1px solid #f0f0f0;

        &:last-child {
          border-bottom: none;
        }

        .anticon {
          font-size: 16px;
          color: @primary-color;
          margin-right: 12px;
        }

        .label {
          color: #64748b;
          margin-right: 8px;
        }

        .value {
          color: #1e3a5f;
          font-weight: 500;
        }
      }
    }
  }

  .edit-card {
    border-radius: 12px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);

    .profile-form,
    .password-form {
      max-width: 500px;

      /deep/ .ant-input,
      /deep/ .ant-input-password {
        border-radius: 8px;
      }

      .email-hint {
        margin-top: 8px;
        font-size: 12px;
        color: rgba(0, 0, 0, 0.45);

        &.email-warning {
          color: #faad14;
        }
      }
    }

    // Credits log amount colors
    .amount-positive {
      color: #52c41a;
      font-weight: 600;
    }

    .amount-negative {
      color: #ff4d4f;
      font-weight: 600;
    }
  }

  // Credits Card 积分卡片
  .credits-card {
    border-radius: 12px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: #fff;

    /deep/ .ant-card-body {
      background: transparent;
      display: flex;
      flex-direction: column;
    }

    /deep/ .ant-divider {
      border-color: rgba(255, 255, 255, 0.2);
    }

    .credits-header {
      .credits-title {
        font-size: 16px;
        font-weight: 600;
        margin: 0;
        color: #fff;
        display: flex;
        align-items: center;
        gap: 8px;

        .anticon {
          font-size: 18px;
        }
      }
    }

    .credits-body {
      padding: 20px 0;
      text-align: center;
      flex: 1;
      display: flex;
      flex-direction: column;
      justify-content: center;

      .credits-amount {
        .amount-value {
          font-size: 42px;
          font-weight: 700;
          color: #fff;
          text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
        }

        .amount-label {
          font-size: 16px;
          color: rgba(255, 255, 255, 0.9);
          margin-left: 8px;
        }
      }

      .vip-status {
        margin-top: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 6px;
        font-size: 13px;

        .vip-active {
          color: #ffd700;
        }

        .vip-expired {
          color: rgba(255, 255, 255, 0.6);
        }

        .no-vip {
          color: rgba(255, 255, 255, 0.7);
        }
      }
    }

    .credits-actions {
      text-align: center;
      margin-top: auto;

      .ant-btn {
        border-radius: 20px;
        padding: 0 24px;
        height: 36px;
        font-weight: 500;
        background: #fff;
        color: #667eea;
        border: none;

        &:hover {
          background: rgba(255, 255, 255, 0.9);
          color: #764ba2;
        }
      }
    }

    .credits-hint {
      margin-top: 12px;
      text-align: center;
      font-size: 12px;
      color: rgba(255, 255, 255, 0.7);
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 6px;
    }
  }

  // Referral Card 邀请卡片
  .referral-card {
    border-radius: 12px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
    background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
    color: #fff;

    /deep/ .ant-card-body {
      background: transparent;
      display: flex;
      flex-direction: column;
    }

    /deep/ .ant-divider {
      border-color: rgba(255, 255, 255, 0.2);
    }

    .referral-header {
      .referral-title {
        font-size: 16px;
        font-weight: 600;
        margin: 0;
        color: #fff;
        display: flex;
        align-items: center;
        gap: 8px;

        .anticon {
          font-size: 18px;
        }
      }
    }

    .referral-body {
      padding: 12px 0;
      flex: 1;
      display: flex;
      flex-direction: column;
      justify-content: space-between;

      .referral-stats {
        display: flex;
        justify-content: space-around;

        .stat-item {
          text-align: center;

          .stat-value {
            font-size: 28px;
            font-weight: 700;
            color: #fff;
            display: block;
          }

          .stat-label {
            font-size: 12px;
            color: rgba(255, 255, 255, 0.8);
          }
        }
      }

      .referral-link-section {
        .link-label {
          font-size: 12px;
          color: rgba(255, 255, 255, 0.9);
          margin-bottom: 6px;
        }

        .link-box {
          /deep/ .ant-input {
            background: rgba(255, 255, 255, 0.2);
            border: 1px solid rgba(255, 255, 255, 0.3);
            color: #fff;

            &::placeholder {
              color: rgba(255, 255, 255, 0.6);
            }
          }

          /deep/ .anticon-copy {
            color: #fff;

            &:hover {
              color: #ffd700;
            }
          }
        }
      }

      .referral-hint {
        margin-top: auto;
        text-align: center;
        font-size: 12px;
        color: rgba(255, 255, 255, 0.85);
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 6px;

        .anticon-gift {
          color: #ffd700;
        }
      }
    }
  }

  // Referral user cell in table
  .referral-user-cell {
    display: flex;
    align-items: center;
    gap: 10px;

    .user-info {
      display: flex;
      flex-direction: column;

      .nickname {
        font-weight: 500;
        color: #333;
      }

      .username {
        font-size: 12px;
        color: #999;
      }
    }
  }

  // Dark theme
  &.theme-dark {
    background: linear-gradient(180deg, #0d1117 0%, #161b22 100%);

    .page-header {
      .page-title {
        color: #e0e6ed;
      }
      .page-desc {
        color: #8b949e;
      }
    }

    .profile-card,
    .edit-card {
      background: #1e222d;
      box-shadow: 0 4px 24px rgba(0, 0, 0, 0.25);

      /deep/ .ant-card-body {
        background: #1e222d;
      }
    }

    .profile-card {
      .avatar-section {
        .username {
          color: #e0e6ed;
        }
      }

      .profile-info {
        .info-item {
          border-bottom-color: #30363d;

          .label {
            color: #8b949e;
          }

          .value {
            color: #e0e6ed;
          }
        }
      }
    }

    .edit-card {
      /deep/ .ant-tabs-bar {
        border-bottom-color: #30363d;
      }

      /deep/ .ant-tabs-tab {
        color: #8b949e;

        &:hover {
          color: #e0e6ed;
        }
      }

      /deep/ .ant-tabs-tab-active {
        color: @primary-color;
      }

      /deep/ .ant-form-item-label label {
        color: #c9d1d9;
      }

      /deep/ .ant-input,
      /deep/ .ant-input-password {
        background: #0d1117;
        border-color: #30363d;
        color: #c9d1d9;

        &:hover,
        &:focus {
          border-color: @primary-color;
        }
      }
    }

    .credits-card {
      background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
      box-shadow: 0 4px 24px rgba(0, 0, 0, 0.25);

      /deep/ .ant-divider {
        border-color: rgba(255, 255, 255, 0.1);
      }

      .credits-actions {
        .ant-btn {
          background: rgba(255, 255, 255, 0.15);
          color: #fff;
          border: 1px solid rgba(255, 255, 255, 0.2);

          &:hover {
            background: rgba(255, 255, 255, 0.25);
          }
        }
      }
    }
  }
}
</style>
