<template>
  <div class="ai-analysis-container" :class="{ 'theme-dark': isDarkTheme }" :style="{ '--primary-color': primaryColor }">
    <!-- 主内容区域 -->
    <div class="main-content">
      <!-- 分析区域 -->
      <div class="analysis-section">
        <!-- 顶部标题和标的选择 -->
        <div class="analysis-header">
          <div class="header-content">
            <div class="center-header-info">
              <div class="logo-section">
                <a-icon type="thunderbolt" theme="twoTone" :twoToneColor="primaryColor" class="logo-icon" />
                <span class="logo-text">QUANT<span class="ant-btn-link">DINGER</span> AI LAB</span>
              </div>
              <div class="status-bar">
                <div class="status-item">
                  <span class="label">SYSTEM:</span>
                  <span class="value online">{{ $t('ai-analysis.system.online') || 'ONLINE' }}</span>
                </div>
                <div class="status-item">
                  <span class="label">{{ $t('ai-analysis.system.agents') || 'AGENTS' }}:</span>
                  <span class="ant-btn-link">13 {{ $t('ai-analysis.system.active') || 'ACTIVE' }}</span>
                </div>
                <div class="status-item">
                  <span class="label">{{ $t('ai-analysis.system.stage') || 'STAGE' }}:</span>
                  <span class="ant-btn-link">{{ analyzing ? 'RUNNING' : 'IDLE' }}</span>
                </div>
              </div>
            </div>
            <div class="symbol-selector-wrapper">
              <a-select
                v-model="selectedSymbol"
                :placeholder="$t('dashboard.analysis.empty.selectSymbol')"
                size="large"
                show-search
                allow-clear
                :filter-option="filterSymbolOption"
                @change="handleSymbolChange"
                @search="handleSymbolSearch"
                :open="symbolSearchOpen"
                @dropdownVisibleChange="handleDropdownVisibleChange"
                class="symbol-selector"
              >
                <!-- 当没有自选股且用户输入时，显示提示选项 -->

                <a-select-option
                  v-for="stock in (watchlist || [])"
                  :key="`${stock.market}-${stock.symbol}`"
                  :value="`${stock.market}:${stock.symbol}`"
                >
                  <span class="symbol-option">
                    <a-tag :color="getMarketColor(stock.market)" style="margin-right: 8px;">
                      {{ getMarketName(stock.market) }}
                    </a-tag>
                    <strong>{{ stock.symbol }}</strong>
                    <span v-if="stock.name" style="color: #999; margin-left: 8px;">{{ stock.name }}</span>
                  </span>
                </a-select-option>
                <a-select-option
                  key="add-stock-option"
                  value="__add_stock_option__"
                  class="add-stock-option"
                >
                  <div style="width: 100%; text-align: center; padding: 4px 0; color: #1890ff; cursor: pointer;">
                    <a-icon type="plus" style="margin-right: 4px;" />
                    <span>{{ $t('dashboard.analysis.watchlist.add') }}</span>
                  </div>
                </a-select-option>
              </a-select>

              <!-- 模型选择器 -->
              <a-select
                v-model="selectedModel"
                :placeholder="$t('dashboard.analysis.selectModel')"
                size="large"
                style="width: 200px;"
                class="model-selector"
              >
                <a-select-option v-for="model in modelOptions" :key="model.value" :value="model.value">
                  {{ model.label }}
                </a-select-option>
              </a-select>

              <a-button
                type="primary"
                size="large"
                icon="thunderbolt"
                @click="startMultiAnalysis"
                :loading="analyzing"
                :disabled="!selectedSymbol"
                class="analyze-button"
              >
                <span>{{ $t('dashboard.analysis.startAnalysis') }}</span>
              </a-button>
              <a-button
                type="default"
                size="large"
                icon="history"
                @click="showHistoryModal = true; loadHistoryList()"
                class="history-button"
                style="margin-left: 12px;"
              >
                <span>{{ $t('dashboard.analysis.history') }}</span>
              </a-button>
            </div>
          </div>
        </div>

        <!-- 空状态和加载展示 (Metaverse Component) -->
        <metaverse-analysis
          :symbol="selectedSymbol"
          :analyzing="analyzing"
          :taskId="currentTaskId"
          :analysisResults="analysisResults"
        />
      </div>

      <!-- 右侧自选股区域 -->
      <div class="watchlist-section">
        <div class="section-header">
          <h3>
            <a-icon type="star" />
            <span>{{ $t('dashboard.analysis.watchlist.title') }}</span>
          </h3>
          <a-button type="link" size="small" @click="showAddStockModal = true">
            <a-icon type="plus" />
            <span>{{ $t('dashboard.analysis.watchlist.add') }}</span>
          </a-button>
        </div>
        <div class="watchlist-container">
          <div
            v-for="stock in (watchlist || [])"
            :key="`${stock.market}-${stock.symbol}`"
            class="watchlist-item"
          >
            <div class="stock-info">
              <div class="stock-symbol">{{ stock.symbol }}</div>
              <div class="stock-name">{{ stock.name || stock.symbol }}</div>
            </div>
            <div class="stock-price">
              <div class="price-value" v-if="stock.price > 0">
                {{ getCurrencySymbol(stock.market) }}{{ formatNumber(stock.price) }}
              </div>
              <div class="price-value" v-else>
                <a-spin size="small" />
              </div>
              <div class="price-change" :class="stock.change >= 0 ? 'positive' : 'negative'" v-if="stock.price > 0">
                <span :class="stock.change >= 0 ? 'up' : 'down'">
                  {{ stock.change >= 0 ? '▲' : '▼' }}{{ Math.abs(stock.changePercent).toFixed(2) }}%
                </span>
              </div>
            </div>
            <a-icon type="close" class="remove-icon" @click.stop="removeFromWatchlist(stock.symbol, stock.market)" />
          </div>
          <div v-if="!watchlist || watchlist.length === 0" class="empty-watchlist">
            <a-empty :description="$t('dashboard.analysis.empty.noWatchlist')" :image="false">
              <a-button type="primary" @click="showAddStockModal = true">
                <a-icon type="plus" />
                {{ $t('dashboard.analysis.watchlist.addStock') }}
              </a-button>
            </a-empty>
          </div>
        </div>
      </div>
    </div>

    <!-- 添加股票弹窗 -->
    <a-modal
      :title="$t('dashboard.analysis.modal.addStock.title')"
      :visible="showAddStockModal"
      @ok="handleAddStock"
      @cancel="handleCloseAddStockModal"
      :confirmLoading="addingStock"
      width="600px"
      :okText="$t('dashboard.analysis.modal.addStock.confirm')"
      :cancelText="$t('dashboard.analysis.modal.addStock.cancel')"
    >
      <div class="add-stock-modal-content">
        <!-- Tab标签 -->
        <a-tabs v-model="selectedMarketTab" @change="handleMarketTabChange" class="market-tabs">
          <a-tab-pane
            v-for="marketType in marketTypes"
            :key="marketType.value"
            :tab="$t(marketType.i18nKey || `dashboard.analysis.market.${marketType.value}`)"
          >
          </a-tab-pane>
        </a-tabs>

        <!-- 搜索/输入框（整合搜索和手动输入） -->
        <div class="symbol-search-section">
          <a-input-search
            v-model="symbolSearchKeyword"
            :placeholder="$t('dashboard.analysis.modal.addStock.searchOrInputPlaceholder')"
            @search="handleSearchOrInput"
            @change="handleSymbolSearchInput"
            :loading="searchingSymbols"
            size="large"
            allow-clear
          >
            <a-button slot="enterButton" type="primary" icon="search">
              {{ $t('dashboard.analysis.modal.addStock.search') }}
            </a-button>
          </a-input-search>
        </div>

        <!-- 搜索结果 -->
        <div v-if="symbolSearchResults.length > 0" class="search-results-section">
          <div class="section-title">
            <a-icon type="search" style="margin-right: 4px;" />
            {{ $t('dashboard.analysis.modal.addStock.searchResults') }}
          </div>
          <a-list
            :data-source="symbolSearchResults"
            :loading="searchingSymbols"
            size="small"
            class="symbol-list"
          >
            <a-list-item slot="renderItem" slot-scope="item" class="symbol-list-item" @click="selectSymbol(item)">
              <a-list-item-meta>
                <template slot="title">
                  <div class="symbol-item-content">
                    <span class="symbol-code">{{ item.symbol }}</span>
                    <span class="symbol-name">{{ item.name }}</span>
                    <a-tag v-if="item.exchange" size="small" color="blue" style="margin-left: 8px;">
                      {{ item.exchange }}
                    </a-tag>
                  </div>
                </template>
              </a-list-item-meta>
            </a-list-item>
          </a-list>
        </div>

        <!-- 热门标的 -->
        <div class="hot-symbols-section">
          <div class="section-title">
            <a-icon type="fire" style="color: #ff4d4f; margin-right: 4px;" />
            {{ $t('dashboard.analysis.modal.addStock.hotSymbols') }}
          </div>
          <a-spin :spinning="loadingHotSymbols">
            <a-list
              v-if="hotSymbols.length > 0"
              :data-source="hotSymbols"
              size="small"
              class="symbol-list"
            >
              <a-list-item slot="renderItem" slot-scope="item" class="symbol-list-item" @click="selectSymbol(item)">
                <a-list-item-meta>
                  <template slot="title">
                    <div class="symbol-item-content">
                      <span class="symbol-code">{{ item.symbol }}</span>
                      <span class="symbol-name">{{ item.name }}</span>
                      <a-tag v-if="item.exchange" size="small" color="orange" style="margin-left: 8px;">
                        {{ item.exchange }}
                      </a-tag>
                    </div>
                  </template>
                </a-list-item-meta>
              </a-list-item>
            </a-list>
            <a-empty v-else :description="$t('dashboard.analysis.modal.addStock.noHotSymbols')" :image="false" />
          </a-spin>
        </div>

        <!-- 选中的标的显示 -->
        <div v-if="selectedSymbolForAdd" class="selected-symbol-section">
          <a-alert
            :message="$t('dashboard.analysis.modal.addStock.selectedSymbol')"
            type="info"
            show-icon
            closable
            @close="selectedSymbolForAdd = null"
          >
            <template slot="description">
              <div class="selected-symbol-info">
                <a-tag :color="getMarketColor(selectedSymbolForAdd.market)" style="margin-right: 8px;">
                  {{ $t(`dashboard.analysis.market.${selectedSymbolForAdd.market}`) }}
                </a-tag>
                <strong>{{ selectedSymbolForAdd.symbol }}</strong>
                <span v-if="selectedSymbolForAdd.name" style="color: #999; margin-left: 8px;">{{ selectedSymbolForAdd.name }}</span>
                <span v-else style="color: #999; margin-left: 8px; font-style: italic;">{{ $t('dashboard.analysis.modal.addStock.nameWillBeFetched') }}</span>
              </div>
            </template>
          </a-alert>
        </div>
      </div>
    </a-modal>

    <!-- 历史分析列表弹窗 -->
    <a-modal
      :title="$t('dashboard.analysis.modal.history.title')"
      :visible="showHistoryModal"
      @cancel="showHistoryModal = false"
      :footer="null"
      width="800px"
      :bodyStyle="{ maxHeight: '60vh', overflowY: 'auto' }"
    >
      <a-spin :spinning="historyLoading">
        <a-list
          :data-source="historyList"
          :pagination="{
            current: historyPage,
            pageSize: historyPageSize,
            total: historyTotal,
            onChange: (page) => { historyPage = page; loadHistoryList() },
            showSizeChanger: true,
            pageSizeOptions: ['10', '20', '50'],
            onShowSizeChange: (current, size) => { historyPageSize = size; historyPage = 1; loadHistoryList() }
          }"
        >
          <a-list-item slot="renderItem" slot-scope="item">
            <a-list-item-meta>
              <template slot="title">
                <div style="display: flex; align-items: center; justify-content: space-between;">
                  <div>
                    <a-tag :color="getMarketColor(item.market)" style="margin-right: 8px;">
                      {{ getMarketName(item.market) }}
                    </a-tag>
                    <strong>{{ item.symbol }}</strong>
                    <a-tag :color="getStatusColor(item.status)" style="margin-left: 12px;">
                      {{ getStatusText(item.status) }}
                    </a-tag>
                  </div>
                  <div>
                    <a-button
                      v-if="item.has_result"
                      type="link"
                      size="small"
                      icon="eye"
                      @click="viewHistoryResult(item)"
                    >
                      {{ $t('dashboard.analysis.modal.history.viewResult') }}
                    </a-button>
                    <a-popconfirm
                      :title="$t('dashboard.analysis.modal.history.deleteConfirm')"
                      :ok-text="$t('common.confirm')"
                      :cancel-text="$t('common.cancel')"
                      @confirm="deleteHistoryItem(item)"
                    >
                      <a-button
                        type="link"
                        size="small"
                        icon="delete"
                        style="color: #ff4d4f;"
                      >
                        {{ $t('dashboard.analysis.modal.history.delete') }}
                      </a-button>
                    </a-popconfirm>
                  </div>
                </div>
              </template>
              <template slot="description">
                <div v-if="item.error_message" style="color: #ff4d4f; font-size: 12px;">
                  {{ $t('dashboard.analysis.modal.history.error') }}: {{ item.error_message }}
                </div>
                <div v-else-if="item.completetime" style="color: #999; font-size: 12px;">
                  {{ $t('dashboard.analysis.modal.history.completeTime') }}: {{ formatTime(item.completetime) }}
                </div>
              </template>
            </a-list-item-meta>
          </a-list-item>
        </a-list>
        <a-empty v-if="!historyLoading && historyList.length === 0" :description="$t('dashboard.analysis.empty.noHistory')" />
      </a-spin>
    </a-modal>
  </div>
</template>

<script>
import { mapGetters, mapState } from 'vuex'
import { getUserInfo } from '@/api/login'
import { getWatchlist, addWatchlist, removeWatchlist, getWatchlistPrices, multiAnalysis, getAnalysisTaskStatus, getAnalysisHistoryList, deleteAnalysisTask, getConfig, getMarketTypes, searchSymbols, getHotSymbols } from '@/api/market'

import MetaverseAnalysis from './components/index'
import { DEFAULT_AI_MODEL_MAP, mergeModelMaps, modelMapToOptions } from '@/config/aiModels'

export default {
  name: 'Analysis',
  components: {
    MetaverseAnalysis
  },
  data () {
    return {
      watchlistPriceTimer: null, // 自选股价格刷新定时器
      localUserInfo: {}, // 本地用户信息（从 API 获取）
      loadingUserInfo: false,
      // Local-only mode: single user (id=1). Keep a default so watchlist works even
      // when user info is loaded asynchronously.
      userId: 1,
      // 自选股数据
      watchlist: [],
      loadingWatchlist: false,
      showAddStockModal: false,
      addingStock: false,
      stockForm: this.$form.createForm(this),
      // 多维度分析相关
      selectedSymbol: undefined, // 当前选中的标的 (格式: "market:symbol")，undefined 时会显示 placeholder
      analyzing: false, // 是否正在分析
      currentTaskId: null, // 当前任务ID
      taskStatusTimer: null, // 任务状态轮询定时器
      symbolSearchValue: '', // 标的选择器搜索输入值
      symbolSearchOpen: false, // 标的选择器下拉框是否打开

      // 模型选择
      selectedModel: 'openai/gpt-4o-mini',
      modelOptions: modelMapToOptions(DEFAULT_AI_MODEL_MAP),

      analysisResults: {
        overview: null,
        fundamental: null,
        technical: null,
        news: null,
        sentiment: null,
        risk: null,
        debate: null,
        trader_decision: null,
        risk_debate: null,
        final_decision: null
      },
      // 历史分析列表
      showHistoryModal: false,
      historyList: [],
      historyLoading: false,
      historyPage: 1,
      historyPageSize: 20,
      historyTotal: 0,
      // 股票类型列表
      marketTypes: [],
      // 添加股票弹窗相关
      selectedMarketTab: '', // 当前选中的市场类型tab
      symbolSearchKeyword: '', // 搜索关键词
      symbolSearchResults: [], // 搜索结果
      searchingSymbols: false, // 是否正在搜索
      hotSymbols: [], // 热门标的列表
      loadingHotSymbols: false, // 是否正在加载热门标的
      selectedSymbolForAdd: null, // 选中的标的（用于添加）
      searchTimer: null, // 搜索防抖定时器
      hasSearched: false // 是否已经搜索过（用于显示无结果提示）
    }
  },
  computed: {
    ...mapGetters(['userInfo']),
    ...mapState({
      navTheme: state => state.app.theme,
      primaryColor: state => state.app.color || '#1890ff'
    }),
    // 判断是否为暗黑主题
    isDarkTheme () {
      return this.navTheme === 'dark' || this.navTheme === 'realdark'
    },
    storeUserInfo () {
      return this.userInfo || {}
    },
    // 合并本地和 store 中的用户信息
    mergedUserInfo () {
      return this.localUserInfo && this.localUserInfo.email ? this.localUserInfo : this.storeUserInfo
    },
    userAvatar () {
      return this.mergedUserInfo?.avatar || ''
    },
    displayUserInfo () {
      return this.mergedUserInfo
    }
  },
  created () {
    this.loadUserInfo()
    this.loadConfig()
    // Local-only mode: load watchlist immediately (userId defaults to 1).
    // This also prevents a blank watchlist if user info fetch is slow/fails.
    this.loadWatchlist()
    // Check for any pending/running analysis tasks from previous session
    this.checkPendingTasks()
  },
  mounted () {
    // 启动自选股价格定时刷新
    this.startWatchlistPriceRefresh()
  },
  beforeDestroy () {
    if (this.watchlistPriceTimer) {
      clearInterval(this.watchlistPriceTimer)
    }
    if (this.taskStatusTimer) {
      clearInterval(this.taskStatusTimer)
    }
  },
  methods: {
    toggleSidebar () {
      // this.sidebarCollapsed = !this.sidebarCollapsed
    },
    // 多维度分析相关方法
    filterSymbolOption (input, option) {
      const value = option.componentOptions?.propsData?.value || ''
      // 如果是提示选项或添加按钮，始终显示
      if (value === '__empty_watchlist_hint__' || value === '__add_stock_option__') {
        return true
      }
      return value.toLowerCase().includes(input.toLowerCase())
    },
    handleSymbolSearch (value) {
      this.symbolSearchValue = value
      // 如果没有自选股且用户输入了内容，打开下拉框
      if (this.watchlist.length === 0 && value) {
        this.symbolSearchOpen = true
      }
    },
    handleDropdownVisibleChange (open) {
      this.symbolSearchOpen = open
      // 如果关闭下拉框，清空搜索值
      if (!open) {
        this.symbolSearchValue = ''
      }
    },
    handleSymbolChange (value) {
      // 如果是提示选项，不处理
      if (value === '__empty_watchlist_hint__') {
        return
      }
      // 如果是添加股票选项
      if (value === '__add_stock_option__') {
        this.showAddStockModal = true
        // 重置选中项，避免显示内部值
        this.$nextTick(() => {
          this.selectedSymbol = undefined
        })
        return
      }
      this.selectedSymbol = value
      // 切换标的时清空分析结果
      this.analysisResults = {
        overview: null,
        fundamental: null,
        technical: null,
        news: null,
        sentiment: null,
        risk: null,
        debate: null,
        trader_decision: null,
        risk_debate: null,
        final_decision: null
      }
    },
    getMarketColor (market) {
      const colors = {
        'USStock': 'green',
        'Crypto': 'purple',
        'Forex': 'gold',
        'Futures': 'cyan',
        'AShare': 'blue',
        'HShare': 'orange'
      }
      return colors[market] || 'default'
    },
    // 获取货币符号
    getCurrencySymbol (market) {
      // 美股、加密货币、外汇、期货：美元
      // A股、港股：人民币
      const dollarMarkets = ['USStock', 'Crypto', 'Forex', 'Futures']
      return dollarMarkets.includes(market) ? '$' : '¥'
    },
    async startMultiAnalysis () {
      if (!this.selectedSymbol) {
        this.$message.warning(this.$t('dashboard.analysis.message.selectSymbol'))
        return
      }

      // Reset state
      this.analyzing = true
      this.currentTaskId = null

      const [market, symbol] = this.selectedSymbol.split(':')
      const language = this.$store.getters.lang || 'zh-CN'
      const useMultiAgent = this.$store.getters.useMultiAgent !== false

      try {
        // Call API to create analysis task
        const res = await multiAnalysis({
          userid: this.userId,
          market: market,
          symbol: symbol,
          language: language,
          use_multi_agent: useMultiAgent,
          model: this.selectedModel,
          timeframe: '1D'
        })

        if (res && res.code === 1 && res.data) {
          if (res.data.task_id) {
            // Task created, start polling for results
            // Frontend will show simulation animation while backend processes
            this.currentTaskId = Number(res.data.task_id) || null
            this.$message.info(this.$t('dashboard.analysis.message.taskCreated') || 'Analysis task created, processing...')
            this.startTaskStatusPolling()
          } else if (res.data.overview || res.data.fundamental || res.data.technical) {
            // Direct result (legacy support)
            this.analysisResults = {
              overview: res.data.overview || null,
              fundamental: res.data.fundamental || null,
              technical: res.data.technical || null,
              news: res.data.news || null,
              sentiment: res.data.sentiment || null,
              risk: res.data.risk || null,
              debate: res.data.debate || null,
              trader_decision: res.data.trader_decision || null,
              risk_debate: res.data.risk_debate || null,
              final_decision: res.data.final_decision || null
            }
            this.$message.success(this.$t('dashboard.analysis.message.analysisComplete'))
            this.analyzing = false
          } else {
            throw new Error('返回数据格式错误')
          }
        } else {
          throw new Error(res?.msg || '创建分析任务失败')
        }
      } catch (error) {
        console.error('Analysis failed:', error)
        const errorMsg = error?.response?.data?.msg || error?.message || this.$t('dashboard.analysis.message.analysisFailed')
        this.$message.error(errorMsg)
        this.analyzing = false
      }
    },
    // 开始轮询任务状态
    startTaskStatusPolling () {
      if (this.taskStatusTimer) {
        clearInterval(this.taskStatusTimer)
      }

      this.taskStatusTimer = setInterval(async () => {
        if (!this.currentTaskId) {
          clearInterval(this.taskStatusTimer)
          return
        }

        try {
          const res = await getAnalysisTaskStatus({
            task_id: this.currentTaskId
          })

          if (res && res.code === 1 && res.data) {
            const task = res.data

            if (task.status === 'completed') {
              // 任务完成，更新分析结果
              this.analysisResults = {
                overview: task.result.overview || null,
                fundamental: task.result.fundamental || null,
                technical: task.result.technical || null,
                news: task.result.news || null,
                sentiment: task.result.sentiment || null,
                risk: task.result.risk || null,
                debate: task.result.debate || null,
                trader_decision: task.result.trader_decision || null,
                risk_debate: task.result.risk_debate || null,
                final_decision: task.result.final_decision || null
              }
              this.$message.success(this.$t('dashboard.analysis.message.analysisComplete'))
              this.analyzing = false
              clearInterval(this.taskStatusTimer)
              this.currentTaskId = null
            } else if (task.status === 'failed') {
              // 任务失败
              this.$message.error(task.error_message || '分析失败')
              this.analyzing = false
              clearInterval(this.taskStatusTimer)
              this.currentTaskId = null
            }
            // processing 状态继续轮询
          }
        } catch (error) {
          // 继续轮询，不中断
        }
      }, 2000) // 每2秒轮询一次
    },
    // 加载历史分析列表
    async loadHistoryList () {
      if (!this.userId) return

      this.historyLoading = true
      try {
        const res = await getAnalysisHistoryList({
          userid: this.userId,
          page: this.historyPage,
          pagesize: this.historyPageSize
        })

        if (res && res.code === 1 && res.data) {
          this.historyList = res.data.list || []
          this.historyTotal = res.data.total || 0
        }
      } catch (error) {
        this.$message.error('加载历史记录失败')
      } finally {
        this.historyLoading = false
      }
    },
    // Check for pending/processing tasks when user returns to page
    async checkPendingTasks () {
      try {
        const res = await getAnalysisHistoryList({
          userid: this.userId,
          page: 1,
          pagesize: 5
        })

        if (res && res.code === 1 && res.data && res.data.list) {
          // Find the most recent pending task
          const pendingTask = res.data.list.find(t => t.status === 'pending')

          if (pendingTask) {
            // There's a pending task - show notification and start polling
            this.currentTaskId = pendingTask.id
            this.selectedSymbol = `${pendingTask.market}:${pendingTask.symbol}`
            this.analyzing = true
            this.$message.info(this.$t('dashboard.analysis.message.resumingAnalysis') || 'Resuming analysis in progress...')
            this.startTaskStatusPolling()
          } else {
            // Check if most recent task just completed (within last 30 seconds)
            const recentCompleted = res.data.list.find(t => {
              if (t.status !== 'completed') return false
              const completedAt = t.completetime
              if (!completedAt) return false
              const now = Math.floor(Date.now() / 1000)
              return (now - completedAt) < 30 // Within 30 seconds
            })

            if (recentCompleted) {
              // Show result of recently completed task
              this.viewHistoryResult(recentCompleted)
            }
          }
        }
      } catch (error) {
        // Silent fail - not critical
        console.warn('Failed to check pending tasks:', error)
      }
    },
    // 查看历史分析结果
    async viewHistoryResult (task) {
      if (task.status !== 'completed') {
        this.$message.warning(this.$t('dashboard.analysis.status.processing'))
        return
      }

      try {
        const res = await getAnalysisTaskStatus({
          task_id: task.id
        })

        if (res && res.code === 1 && res.data && res.data.result) {
          // 设置选中的标的
          this.selectedSymbol = `${res.data.market}:${res.data.symbol}`

          // 更新分析结果
          this.analysisResults = {
            overview: res.data.result.overview || null,
            fundamental: res.data.result.fundamental || null,
            technical: res.data.result.technical || null,
            news: res.data.result.news || null,
            sentiment: res.data.result.sentiment || null,
            risk: res.data.result.risk || null,
            debate: res.data.result.debate || null,
            trader_decision: res.data.result.trader_decision || null,
            risk_debate: res.data.result.risk_debate || null,
            final_decision: res.data.result.final_decision || null
          }

          // 关闭历史列表弹窗
          this.showHistoryModal = false
          this.$message.success(this.$t('dashboard.analysis.message.analysisComplete'))
        }
      } catch (error) {
        this.$message.error(this.$t('dashboard.analysis.message.analysisFailed'))
      }
    },
    // Delete history item
    async deleteHistoryItem (item) {
      try {
        const res = await deleteAnalysisTask({ task_id: item.id })
        if (res && res.code === 1) {
          this.$message.success(this.$t('dashboard.analysis.message.deleteSuccess'))
          this.loadHistoryList()
        } else {
          this.$message.error(res?.msg || this.$t('dashboard.analysis.message.deleteFailed'))
        }
      } catch (error) {
        this.$message.error(this.$t('dashboard.analysis.message.deleteFailed'))
      }
    },
    // 格式化时间
    formatTime (timestamp) {
      if (!timestamp) return '-'
      const date = new Date(timestamp * 1000)
      return date.toLocaleString('zh-CN')
    },
    // 获取状态标签颜色
    getStatusColor (status) {
      const colors = {
        'pending': 'orange',
        'processing': 'blue',
        'completed': 'green',
        'failed': 'red'
      }
      return colors[status] || 'default'
    },
    // 获取状态文本
    getStatusText (status) {
      const statusMap = {
        'pending': 'dashboard.analysis.status.pending',
        'processing': 'dashboard.analysis.status.processing',
        'completed': 'dashboard.analysis.status.completed',
        'failed': 'dashboard.analysis.status.failed'
      }
      const key = statusMap[status]
      return key ? this.$t(key) : status
    },
    async loadUserInfo () {
      this.loadingUserInfo = true
      try {
        // 先从 store 获取
        if (this.storeUserInfo && this.storeUserInfo.email) {
          this.localUserInfo = this.storeUserInfo
          this.userId = this.storeUserInfo.id
          this.loadingUserInfo = false
          // 加载数据
          this.loadWatchlist()
          return
        }
        // 如果 store 中没有，从 API 获取
        const res = await getUserInfo()
        if (res && res.code === 1 && res.data) {
          this.localUserInfo = res.data
          this.userId = res.data.id
          // 更新 store
          this.$store.commit('SET_INFO', res.data)
          // 加载数据
          this.loadWatchlist()
        }
      } catch (error) {
      } finally {
        this.loadingUserInfo = false
      }
    },
    // 加载自选股
    async loadWatchlist () {
      if (!this.userId) return
      this.loadingWatchlist = true
      try {
        const res = await getWatchlist({ userid: this.userId })
        if (res && res.code === 1 && res.data) {
          this.watchlist = res.data.map(item => ({
            ...item,
            price: 0,
            change: 0,
            changePercent: 0
          }))
          // 加载价格数据
          await this.loadWatchlistPrices()
        }
      } catch (error) {
        this.$message.error(this.$t('dashboard.analysis.message.addStockFailed'))
      } finally {
        this.loadingWatchlist = false
      }
    },
    // 加载自选股价格
    async loadWatchlistPrices () {
      if (!this.watchlist || this.watchlist.length === 0) return

      try {
        // 构建请求数据
        const watchlistData = this.watchlist.map(item => ({
          market: item.market,
          symbol: item.symbol
        }))

        // 通过 PHP 接口调用 Python API 获取价格
        const res = await getWatchlistPrices({
          watchlist: watchlistData
        })

        if (res && res.code === 1 && res.data) {
          const priceMap = {}
          res.data.forEach(item => {
            priceMap[`${item.market}-${item.symbol}`] = item
          })

          // 更新价格数据
          this.watchlist = this.watchlist.map(item => {
            const key = `${item.market}-${item.symbol}`
            const priceData = priceMap[key]
            if (priceData) {
              return {
                ...item,
                price: priceData.price || 0,
                change: priceData.change || 0,
                changePercent: priceData.changePercent || 0
              }
            }
            return item
          })
        }
      } catch (error) {
        // 不显示错误提示，避免干扰用户体验
      }
    },
    // 启动自选股价格定时刷新
    startWatchlistPriceRefresh () {
      // 每30秒刷新一次价格
      this.watchlistPriceTimer = setInterval(() => {
        if (this.watchlist && this.watchlist.length > 0) {
          this.loadWatchlistPrices()
        }
      }, 30000)

      // 立即加载一次
      if (this.watchlist && this.watchlist.length > 0) {
        this.loadWatchlistPrices()
      }
    },
    // 添加自选股
    async handleAddStock () {
      let market = ''
      let symbol = ''
      let name = ''

      // 检查是否选中了标的（从数据库选择或手动输入）
      if (this.selectedSymbolForAdd) {
        market = this.selectedSymbolForAdd.market
        symbol = this.selectedSymbolForAdd.symbol.toUpperCase()
        name = this.selectedSymbolForAdd.name || ''
      } else if (this.symbolSearchKeyword && this.symbolSearchKeyword.trim()) {
        // 如果没有选中，但搜索框有输入，使用搜索框的值
        if (!this.selectedMarketTab) {
          this.$message.warning(this.$t('dashboard.analysis.modal.addStock.pleaseSelectMarket'))
          return
        }
        market = this.selectedMarketTab
        symbol = this.symbolSearchKeyword.trim().toUpperCase()
        name = ''
      } else {
        this.$message.warning(this.$t('dashboard.analysis.modal.addStock.pleaseSelectOrEnterSymbol'))
        return
      }

      this.addingStock = true
      try {
        const res = await addWatchlist({
          userid: this.userId,
          market: market,
          symbol: symbol,
          name: name
        })
        if (res && res.code === 1) {
          this.$message.success(this.$t('dashboard.analysis.message.addStockSuccess'))
          this.handleCloseAddStockModal()
          // 重新加载自选股
          await this.loadWatchlist()
        } else {
          this.$message.error(res?.msg || this.$t('dashboard.analysis.message.addStockFailed'))
        }
      } catch (error) {
        // 如果错误信息包含QDT相关提示，直接显示；否则显示默认错误
        const errorMsg = error?.response?.data?.msg || error?.message || this.$t('dashboard.analysis.message.addStockFailed')
        this.$message.error(errorMsg)
      } finally {
        this.addingStock = false
      }
    },
    // 关闭添加股票弹窗
    handleCloseAddStockModal () {
      this.showAddStockModal = false
      this.selectedSymbolForAdd = null
      this.symbolSearchKeyword = ''
      this.symbolSearchResults = []
      this.hasSearched = false
      this.selectedMarketTab = this.marketTypes.length > 0 ? this.marketTypes[0].value : ''
    },
    // 市场类型Tab切换
    handleMarketTabChange (activeKey) {
      this.selectedMarketTab = activeKey
      this.symbolSearchKeyword = ''
      this.symbolSearchResults = []
      this.selectedSymbolForAdd = null
      this.hasSearched = false
      // 加载该市场类型的热门标的
      this.loadHotSymbols(activeKey)
    },
    // 搜索标的输入变化（防抖）
    handleSymbolSearchInput (e) {
      const keyword = e.target.value
      this.symbolSearchKeyword = keyword

      // 清除之前的定时器
      if (this.searchTimer) {
        clearTimeout(this.searchTimer)
      }

      // 如果关键词为空，清空搜索结果和状态
      if (!keyword || keyword.trim() === '') {
        this.symbolSearchResults = []
        this.hasSearched = false
        this.selectedSymbolForAdd = null
        return
      }

      // 防抖：500ms后执行搜索
      this.searchTimer = setTimeout(() => {
        this.searchSymbolsInModal(keyword)
      }, 500)
    },
    // 搜索或直接添加（整合逻辑）
    handleSearchOrInput (keyword) {
      if (!keyword || !keyword.trim()) {
        return
      }

      if (!this.selectedMarketTab) {
        this.$message.warning(this.$t('dashboard.analysis.modal.addStock.pleaseSelectMarket'))
        return
      }

      // 如果有搜索结果，不处理（让用户选择）
      if (this.symbolSearchResults.length > 0) {
        return
      }

      // 如果没有搜索结果，直接添加
      if (this.hasSearched && this.symbolSearchResults.length === 0) {
        this.handleDirectAdd()
      } else {
        // 执行搜索
        this.searchSymbolsInModal(keyword)
      }
    },
    // 搜索标的（在添加股票弹窗中）
    async searchSymbolsInModal (keyword) {
      if (!keyword || keyword.trim() === '') {
        this.symbolSearchResults = []
        this.hasSearched = false
        return
      }

      if (!this.selectedMarketTab) {
        this.$message.warning(this.$t('dashboard.analysis.modal.addStock.pleaseSelectMarket'))
        return
      }

      this.searchingSymbols = true
      this.hasSearched = true
      try {
        const res = await searchSymbols({
          market: this.selectedMarketTab,
          keyword: keyword.trim(),
          limit: 20
        })
        if (res && res.code === 1 && res.data && res.data.length > 0) {
          this.symbolSearchResults = res.data
        } else {
          // 搜索无结果，不报错，允许直接添加
          this.symbolSearchResults = []
          // 自动设置为手动输入模式
          this.selectedSymbolForAdd = {
            market: this.selectedMarketTab,
            symbol: keyword.trim().toUpperCase(),
            name: '' // 名称由后端通过API获取
          }
        }
      } catch (error) {
        // 搜索失败也不报错，允许直接添加
        this.symbolSearchResults = []
        this.selectedSymbolForAdd = {
          market: this.selectedMarketTab,
          symbol: keyword.trim().toUpperCase(),
          name: '' // 名称由后端通过API获取
        }
      } finally {
        this.searchingSymbols = false
      }
    },
    // 直接添加（搜索无结果时）
    handleDirectAdd () {
      if (!this.symbolSearchKeyword || !this.symbolSearchKeyword.trim()) {
        this.$message.warning(this.$t('dashboard.analysis.modal.addStock.pleaseEnterSymbol'))
        return
      }

      if (!this.selectedMarketTab) {
        this.$message.warning(this.$t('dashboard.analysis.modal.addStock.pleaseSelectMarket'))
        return
      }

      // 设置选中的标的（手动输入，名称会在后端获取）
      this.selectedSymbolForAdd = {
        market: this.selectedMarketTab,
        symbol: this.symbolSearchKeyword.trim().toUpperCase(),
        name: '' // 名称由后端通过API获取
      }
    },
    // 选择标的
    selectSymbol (symbol) {
      this.selectedSymbolForAdd = {
        market: symbol.market,
        symbol: symbol.symbol,
        name: symbol.name || symbol.symbol
      }
    },
    // 加载热门标的
    async loadHotSymbols (market) {
      if (!market) {
        market = this.selectedMarketTab || (this.marketTypes.length > 0 ? this.marketTypes[0].value : '')
      }

      if (!market) {
        return
      }

      this.loadingHotSymbols = true
      try {
        const res = await getHotSymbols({
          market: market,
          limit: 10
        })
        if (res && res.code === 1 && res.data) {
          this.hotSymbols = res.data
        } else {
          this.hotSymbols = []
        }
      } catch (error) {
        this.hotSymbols = []
      } finally {
        this.loadingHotSymbols = false
      }
    },
    // 删除自选股
    async removeFromWatchlist (symbol, market) {
      if (!this.userId) return
      try {
        const res = await removeWatchlist({
          userid: this.userId,
          symbol: symbol
        })
        if (res && res.code === 1) {
          this.$message.success(this.$t('dashboard.analysis.message.removeStockSuccess'))
          // 重新加载自选股
          await this.loadWatchlist()
        } else {
          this.$message.error(res?.msg || this.$t('dashboard.analysis.message.removeStockFailed'))
        }
      } catch (error) {
        this.$message.error(this.$t('dashboard.analysis.message.removeStockFailed'))
      }
    },
    // 获取市场名称
    getMarketName (market) {
      return this.$t(`dashboard.analysis.market.${market}`) || market
    },
    // 格式化数字
    formatNumber (num) {
      if (typeof num === 'string') {
        return num
      }
      return num.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
    },
    // 加载配置
    async loadConfig () {
      try {
        const res = await getConfig()
        if (res && res.code === 1 && res.data && res.data.models) {
          const mergedModels = mergeModelMaps(DEFAULT_AI_MODEL_MAP, res.data.models)
          this.modelOptions = modelMapToOptions(mergedModels)

          // 如果当前选中的模型不在列表中，且列表不为空，则默认选中第一个
          if (this.modelOptions.length > 0 && !this.modelOptions.find(m => m.value === this.selectedModel)) {
            this.selectedModel = this.modelOptions[0].value
          }
        }
      } catch (error) {
      }
      // 加载股票类型列表
      await this.loadMarketTypes()
    },
    // 加载股票类型列表
    async loadMarketTypes () {
      try {
        const res = await getMarketTypes()
        if (res && res.code === 1 && res.data && Array.isArray(res.data)) {
          // 如果返回的是数组格式 [{value: 'AShare', i18nKey: 'dashboard.analysis.market.AShare'}, ...]
          this.marketTypes = res.data.map(item => ({
            value: item.value,
            i18nKey: item.i18nKey || `dashboard.analysis.market.${item.value}`
          }))
        } else if (res && res.code === 1 && res.data && typeof res.data === 'object') {
          // 如果返回的是对象格式 {AShare: 'A股', USStock: '美股', ...}（兼容旧格式）
          this.marketTypes = Object.keys(res.data).map(key => ({
            value: key,
            i18nKey: `dashboard.analysis.market.${key}`
          }))
        } else {
          // 如果获取失败，使用默认值 (Order: USStock > Crypto > Forex > Futures > HShare > AShare)
          this.marketTypes = [
            { value: 'USStock', i18nKey: 'dashboard.analysis.market.USStock' },
            { value: 'Crypto', i18nKey: 'dashboard.analysis.market.Crypto' },
            { value: 'Forex', i18nKey: 'dashboard.analysis.market.Forex' },
            { value: 'Futures', i18nKey: 'dashboard.analysis.market.Futures' },
            { value: 'HShare', i18nKey: 'dashboard.analysis.market.HShare' },
            { value: 'AShare', i18nKey: 'dashboard.analysis.market.AShare' }
          ]
        }
      } catch (error) {
        // 如果获取失败，使用默认值 (Order: USStock > Crypto > Forex > Futures > HShare > AShare)
        this.marketTypes = [
          { value: 'USStock', i18nKey: 'dashboard.analysis.market.USStock' },
          { value: 'Crypto', i18nKey: 'dashboard.analysis.market.Crypto' },
          { value: 'Forex', i18nKey: 'dashboard.analysis.market.Forex' },
          { value: 'Futures', i18nKey: 'dashboard.analysis.market.Futures' },
          { value: 'HShare', i18nKey: 'dashboard.analysis.market.HShare' },
          { value: 'AShare', i18nKey: 'dashboard.analysis.market.AShare' }
        ]
      }

      // 初始化选中的市场类型tab
      if (this.marketTypes.length > 0 && !this.selectedMarketTab) {
        this.selectedMarketTab = this.marketTypes[0].value
      }
    }
  },
  watch: {
    // 监听弹窗打开，初始化数据
    showAddStockModal (newVal) {
      if (newVal) {
        // 初始化选中的市场类型
        if (this.marketTypes.length > 0 && !this.selectedMarketTab) {
          this.selectedMarketTab = this.marketTypes[0].value
        }
        // 加载热门标的
        if (this.selectedMarketTab) {
          this.loadHotSymbols(this.selectedMarketTab)
        }
      } else {
        // 关闭时清理数据
        this.selectedSymbolForAdd = null
        this.symbolSearchKeyword = ''
        this.symbolSearchResults = []
        this.hasSearched = false
        if (this.searchTimer) {
          clearTimeout(this.searchTimer)
          this.searchTimer = null
        }
      }
    }
  }
}
</script>

<style lang="less" scoped>
.ai-analysis-container {
  display: flex;
  height: calc(100vh - 120px); // 减去顶部导航栏高度
  background: #f0f2f5;
  overflow: hidden; // 防止容器本身滚动
  width: 100%;
  // max-width: 100%;
  box-sizing: border-box;
}
@media (max-width: 768px) {
.ai-analysis-container {
  display: flex;
  height: calc(100vh - 120px); // 减去顶部导航栏高度
  background: #f0f2f5;
  overflow: hidden; // 防止容器本身滚动
  width: calc(100% + 44px)!important;
  // max-width: 100%;
  margin: -22px;
  box-sizing: border-box;
}
}
// Removed .sidebar related styles

.main-content {
  flex: 1;
  display: flex;
  gap: 20px;
  overflow: hidden;
  background: #f5f5f5;
  padding: 0px;
  height: 100%;
  min-width: 0; // 允许 flex 子元素收缩
  width: 0; // 配合 flex: 1 使用，确保正确收缩
  box-sizing: border-box;
}

// 分析区域
.analysis-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: #fff;
  border-radius: 12px;
  padding: 24px;
  gap: 24px;
  height: 100%;
  min-height: 0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  position: relative;
  overflow: hidden;
  box-sizing: border-box;
  width: 100%;
  max-width: 100%;

  // 科技感动态背景层
  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background:
      linear-gradient(135deg, rgba(24, 144, 255, 0.03) 0%, rgba(102, 126, 234, 0.03) 50%, rgba(135, 206, 250, 0.02) 100%),
      radial-gradient(circle at 20% 30%, rgba(24, 144, 255, 0.05) 0%, transparent 50%),
      radial-gradient(circle at 80% 70%, rgba(102, 126, 234, 0.05) 0%, transparent 50%);
    background-size: 100% 100%, 800px 800px, 600px 600px;
    background-position: 0 0, 0 0, 100% 100%;
    animation: backgroundShift 20s ease-in-out infinite;
    z-index: 0;
    pointer-events: none;
  }

  // 动态网格背景
  &::after {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-image:
      linear-gradient(rgba(24, 144, 255, 0.03) 1px, transparent 1px),
      linear-gradient(90deg, rgba(24, 144, 255, 0.03) 1px, transparent 1px);
    background-size: 40px 40px;
    background-position: 0 0, 0 0;
    animation: gridMove 30s linear infinite;
    z-index: 0;
    pointer-events: none;
    opacity: 0.6;
  }

  // 确保内容在背景之上
  > * {
    position: relative;
    z-index: 1;
  }

  .center-header-info {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 24px;
    padding-bottom: 20px;
    border-bottom: 1px solid rgba(0, 0, 0, 0.06);

    .logo-section {
      font-size: 24px;
      font-weight: 700;
      letter-spacing: 1px;
      display: flex;
      align-items: center;
      gap: 10px;
      .logo-icon { font-size: 32px; }
      .logo-text { color: #262626; }
      .highlight { color: var(--primary-color); }
    }

    .status-bar {
      display: flex;
      gap: 24px;
      font-size: 13px;

      .status-item {
        display: flex;
        gap: 8px;
        align-items: center;
        .label { color: #8c8c8c; font-weight: 600; }
        .value { color: var(--primary-color); font-weight: bold; font-family: 'Orbitron', sans-serif; }
        .value.online { color: #52c41a; }
      }
    }
  }

  .analysis-header {
    position: relative;
    z-index: 1;

    .header-content {
      .title-section {
        margin-bottom: 24px;

        .main-title {
          font-size: 28px;
          font-weight: 700;
          margin: 0 0 8px 0;
          color: #262626;
          line-height: 1.2;
          display: flex;
          align-items: center;
          gap: 12px;

          .title-icon {
            font-size: 32px;
            animation: pulse 2s ease-in-out infinite;
          }
        }

        .title-subtitle {
          font-size: 14px;
          color: #8c8c8c;
          margin: 0;
          font-weight: 400;
        }
      }

      .symbol-selector-wrapper {
        display: flex;
        gap: 12px;
        margin-bottom: 24px;
        flex-wrap: wrap;

        .symbol-selector {
          flex: 1;
          min-width: 200px;
        }

        .analyze-button {
          height: 40px;
          padding: 0 24px;
          font-weight: 600;
          flex-shrink: 0;
        }

        .history-button {
          flex-shrink: 0;
        }

        .symbol-option {
          display: flex;
          align-items: center;
        }
      }

      // 空自选股提示选项样式
      ::v-deep .empty-watchlist-hint-option {
        .ant-select-item-option-content {
          padding: 0;
        }

        .empty-watchlist-hint {
          display: flex;
          align-items: center;
          padding: 8px 12px;
          color: #595959;
          font-size: 14px;

          .anticon {
            color: var(--primary-color);
            margin-right: 8px;
          }

          .ant-btn-link {
            padding: 0;
            height: auto;
            line-height: 1.5;
            font-size: 14px;
            color: var(--primary-color) !important;
            transition: color 0.3s;

            &:hover {
              color: var(--primary-color) !important;
              opacity: 0.8;
            }
          }
        }
      }
    }
  }
}

// 右侧自选股区域
.watchlist-section {
  width: 320px;
  min-width: 280px;
  background: #fff;
  border-radius: 12px;
  padding: 24px;
  border: 1px solid #e8e8e8;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  height: 100%;
  min-height: 0;
  position: relative;
  flex-shrink: 0;
  box-sizing: border-box;
  max-width: 100%;

  .section-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 8px;

    h3 {
      font-size: 18px;
      font-weight: 600;
      margin: 0;
      display: flex;
      align-items: center;
      gap: 8px;
      color: #262626;
      font-weight: 700;

      .anticon {
        color: #1890ff;
        font-size: 20px;
      }
    }
  }

  .watchlist-container {
    flex: 1;
    overflow-y: auto;
    overflow-x: hidden;
    min-height: 0; // 允许 flex 子元素收缩

    // 隐藏滚动条但保持滚动功能
    scrollbar-width: none; // Firefox
    -ms-overflow-style: none; // IE 和 Edge

    &::-webkit-scrollbar {
      display: none; // Chrome, Safari, Opera
    }

    .watchlist-item {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 12px;
      margin-bottom: 8px;
      background: #fafafa;
      border-radius: 8px;
      border: 1px solid #e8e8e8;
      transition: all 0.3s;

      &:hover {
        background: #f0f0f0;
        border-color: #1890ff;

        .remove-icon {
          opacity: 1;
        }
      }

      .stock-info {
        flex: 1;

        .stock-symbol {
          font-size: 16px;
          font-weight: 600;
          color: #262626;
          margin-bottom: 4px;
        }

        .stock-name {
          font-size: 12px;
          color: #999;
        }

        .stock-market {
          font-size: 10px;
          color: #1890ff;
          background: #e6f7ff;
          padding: 2px 6px;
          border-radius: 2px;
          display: inline-block;
          margin-top: 4px;
        }
      }

      .stock-price {
        text-align: right;
        margin-right: 12px;

        .price-value {
          font-size: 16px;
          font-weight: 600;
          color: #262626;
          margin-bottom: 4px;
        }

        .price-change {
          font-size: 12px;
          font-weight: 600;

          .up {
            color: #52c41a;
          }

          .down {
            color: #ff4d4f;
          }
        }
      }

      .remove-icon {
        cursor: pointer;
        color: #ff4d4f;
        font-size: 14px;
        opacity: 0;
        transition: opacity 0.3s;

        &:hover {
          color: #cf1322;
        }
      }
    }

    .empty-watchlist {
      padding: 40px 0;
      text-align: center;
    }
  }
}

// 消息样式（在问答区域中使用）
.messages-list {
  .message-item {
    display: flex;
    margin-bottom: 24px;
    animation: fadeIn 0.3s;

    &.user-message {
      flex-direction: row-reverse;

      .message-content {
        background: #1890ff;
        color: #fff;
        margin-right: 12px;
        margin-left: 0;
      }
    }

    &.ai-message {
      .message-content {
        background: #fff;
        color: #262626;
        margin-left: 12px;
        margin-right: 0;
        border: 1px solid #e8e8e8;
      }
    }

    &.loading {
      .message-content {
        display: flex;
        align-items: center;
        gap: 8px;
      }
    }

    .message-avatar {
      flex-shrink: 0;
    }

    .message-content {
      max-width: 75%;
      padding: 12px 16px;
      border-radius: 8px;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);

      .message-text {
        line-height: 1.6;
        word-wrap: break-word;
      }

      .message-time {
        font-size: 12px;
        color: #8c8c8c;
        margin-top: 8px;
      }

      .ai-report {
        margin-top: 16px;

        .report-card {
          background: #f5f5f5;
        }

        .report-content {
          .report-section {
            margin-bottom: 16px;

            h4 {
              font-size: 14px;
              font-weight: bold;
              margin-bottom: 8px;
            }

            p {
              font-size: 13px;
              line-height: 1.6;
              margin-bottom: 8px;
            }

            .recommendation {
              margin-top: 8px;
            }
          }
        }
      }
    }
  }
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.8;
    transform: scale(1.1);
  }
}

@keyframes rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

// 科技感背景动画
@keyframes backgroundShift {
  0%, 100% {
    background-position: 0 0, 0 0, 100% 100%;
    opacity: 1;
  }
  50% {
    background-position: 0 0, 20% 20%, 80% 80%;
    opacity: 0.8;
  }
}

@keyframes gridMove {
  0% {
    background-position: 0 0, 0 0;
  }
  100% {
    background-position: 40px 40px, 40px 40px;
  }
}

// 响应式设计
@media (max-width: 1400px) {
  .main-content {
    padding: 16px;
    gap: 16px;
  }

  .analysis-section {
    padding: 20px;
    gap: 20px;
  }

  .watchlist-section {
    width: 280px;
    min-width: 260px;
    padding: 20px;
  }
}

@media (max-width: 1200px) {
  // Removed .sidebar styles

  .main-content {
    padding: 12px;
    gap: 12px;
  }

  .analysis-section {
    padding: 16px;
    gap: 16px;

    .analysis-header {
      .header-content {
        .title-section {
          .main-title {
            font-size: 24px;
          }
        }
      }
    }
  }

  .watchlist-section {
    width: 260px;
    min-width: 240px;
    padding: 16px;
  }
}

@media (max-width: 992px) {
  .ai-analysis-container {
    flex-direction: column;
    height: auto;
    min-height: calc(100vh - 64px);
    overflow-y: auto;
    overflow-x: hidden;
  }

  // Removed .sidebar styles

  .main-content {
    flex-direction: column;
    height: auto;
    padding: 0px;
    gap: 12px;
    width: 100% !important;
    min-width: 100% !important;
    overflow-x: hidden;
  }

  .analysis-section {
    width: 100% !important;
    min-width: 100% !important;
    max-width: 100% !important;
    height: auto;
    min-height: 500px;
    flex-shrink: 0;

    .center-header-info {
      flex-direction: column;
      align-items: flex-start;
      gap: 16px;
      margin-bottom: 16px;
      padding-bottom: 16px;

      .logo-section {
        font-size: 20px;
        width: 100%;

        .logo-icon {
          font-size: 28px;
        }
      }

      .status-bar {
        flex-wrap: nowrap;
        gap: 8px;
        font-size: 12px;
        width: 100%;
        overflow-x: auto;

        .status-item {
          gap: 4px;
          flex-shrink: 0;
          white-space: nowrap;
        }
      }
    }
  }

  .watchlist-section {
    width: 100% !important;
    min-width: 100% !important;
    max-width: 100% !important;
    height: auto;
    max-height: 400px;
    order: -1;
    flex-shrink: 0;
  }

  .symbol-selector-wrapper {
    flex-direction: column;
    width: 100%;
    gap: 8px;

    .symbol-selector {
      width: 100% !important;
      min-width: 100% !important;
      max-width: 100% !important;
      margin-bottom: 0;
    }

    .model-selector {
      width: 100% !important;
    }

    .analyze-button,
    .history-button {
      width: 100%;
      height: 44px;
      padding: 0 16px;
      font-size: 14px;
      flex: none;
      min-width: 0;
      margin-left: 0 !important;
    }
  }
}

@media (max-width: 768px) {
  .ai-analysis-container {
    height: auto;
    min-height: calc(100vh - 64px);
    overflow-y: auto;
    overflow-x: hidden;
  }

  // Removed .sidebar styles

  .main-content {
    padding: 8px;
    gap: 8px;
    width: 100% !important;
    min-width: 100% !important;
    overflow-x: hidden;
  }

  .analysis-section {
    width: 100% !important;
    min-width: 100% !important;
    max-width: 100% !important;
    padding: 12px;
    gap: 12px;
    border-radius: 8px;

    .center-header-info {
      flex-direction: column;
      align-items: flex-start;
      gap: 12px;
      margin-bottom: 12px;
      padding-bottom: 12px;

      .logo-section {
        font-size: 18px;
        width: 100%;

        .logo-icon {
          font-size: 24px;
        }

        .logo-text {
          font-size: 16px;
          line-height: 1.4;
        }
      }

      .status-bar {
        flex-wrap: nowrap;
        gap: 6px;
        font-size: 12px;
        width: 100%;
        overflow-x: auto;

        .status-item {
          gap: 3px;
          flex-shrink: 0;
          white-space: nowrap;

          .label {
            font-size: 10px;
          }

          .value {
            font-size: 12px;
          }
        }
      }
    }

    .analysis-header {
      .header-content {
        .title-section {
          margin-bottom: 16px;

          .main-title {
            font-size: 20px;
            flex-wrap: wrap;

            .title-icon {
              font-size: 24px;
            }
          }

          .title-subtitle {
            font-size: 12px;
          }
        }

        .symbol-selector-wrapper {
          gap: 8px;

          .symbol-selector {
            width: 100% !important;
          }

          .model-selector {
            width: 100% !important;
          }

          .analyze-button,
          .history-button {
            width: 100%;
            height: 40px;
            font-size: 13px;
            padding: 0 12px;
          }
        }
      }
    }

  }

  .watchlist-section {
    width: 100% !important;
    min-width: 100% !important;
    max-width: 100% !important;
    padding: 12px;
    border-radius: 8px;
    max-height: 350px;

    .section-header {
      h3 {
        font-size: 16px;
      }
    }

    .watchlist-item {
      padding: 10px;

      .stock-info {
        .stock-symbol {
          font-size: 14px;
        }

        .stock-name {
          font-size: 11px;
        }
      }

      .stock-price {
        .price-value {
          font-size: 14px;
        }
      }
    }
  }
}

@media (max-width: 576px) {
  .ai-analysis-container {
    padding: 0;
  }

  // Removed .sidebar styles

  .main-content {
    padding: 4px;
    gap: 4px;
    width: 100% !important;
    min-width: 100% !important;
  }

  .analysis-section {
    width: 100% !important;
    min-width: 100% !important;
    max-width: 100% !important;
    padding: 8px;
    gap: 8px;

    .center-header-info {
      flex-direction: column;
      align-items: flex-start;
      gap: 10px;
      margin-bottom: 10px;
      padding-bottom: 10px;

      .logo-section {
        font-size: 16px;
        width: 100%;

        .logo-icon {
          font-size: 20px;
        }

        .logo-text {
          font-size: 14px;
          line-height: 1.3;
          word-break: break-word;
        }
      }

      .status-bar {
        flex-wrap: nowrap;
        gap: 4px;
        font-size: 12px;
        width: 100%;
        overflow-x: auto;

        .status-item {
          gap: 3px;
          flex-shrink: 0;
          white-space: nowrap;

          .label {
            font-size: 10px;
          }

          .value {
            font-size: 12px;
          }
        }
      }
    }

    .analysis-header {
      .header-content {
        .title-section {
          .main-title {
            font-size: 18px;
          }
        }

        .symbol-selector-wrapper {
          flex-direction: column;
          width: 100%;
          gap: 6px;

          .symbol-selector {
            width: 100% !important;
            min-width: 100% !important;
            max-width: 100% !important;
          }

          .model-selector {
            width: 100% !important;
          }

          .analyze-button,
          .history-button {
            width: 100%;
            height: 40px;
            font-size: 13px;
            padding: 0 12px;
            margin-left: 0 !important;
            margin-top: 0;

            span {
              display: inline;
            }
          }
        }
      }
    }

  }

  .watchlist-section {
    width: 100% !important;
    min-width: 100% !important;
    max-width: 100% !important;
    padding: 8px;

    .section-header {
      h3 {
        font-size: 14px;

        .anticon {
          font-size: 16px;
        }
      }
    }
  }
}

@media (max-width: 480px) {
  .analysis-section {
    padding: 6px;
    gap: 6px;

    .center-header-info {
      gap: 8px;
      margin-bottom: 8px;
      padding-bottom: 8px;

      .logo-section {
        font-size: 14px;

        .logo-icon {
          font-size: 18px;
        }

        .logo-text {
          font-size: 12px;
        }
      }

      .status-bar {
        flex-wrap: nowrap;
        gap: 3px;
        font-size: 12px;
        width: 100%;
        overflow-x: auto;

        .status-item {
          flex-shrink: 0;
          white-space: nowrap;
          gap: 2px;

          .label {
            font-size: 10px;
          }

          .value {
            font-size: 12px;
          }
        }
      }
    }

    .analysis-header {
      .header-content {
        .title-section {
          .main-title {
            font-size: 16px;

            .title-icon {
              font-size: 20px;
            }
          }

          .title-subtitle {
            font-size: 11px;
          }
        }

        .symbol-selector-wrapper {
          gap: 6px;

          .symbol-selector {
            ::v-deep .ant-select-selection {
              font-size: 13px;
            }
          }

          .model-selector {
            ::v-deep .ant-select-selection {
              font-size: 13px;
            }
          }

          .analyze-button,
          .history-button {
            width: 100%;
            height: 38px;
            font-size: 12px;
            padding: 0 10px;
            margin-top: 0;
          }
        }
      }
    }
  }
}

/* ========== 暗黑主题样式 ========== */
.ai-analysis-container.theme-dark,
:global(body.dark) .ai-analysis-container,
:global(body.realdark) .ai-analysis-container {
  background: #131722;
  color: #d1d4dc;

  .main-content {
    background: #131722;
  }

  .analysis-section {
    background: #1e222d;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);

    .center-header-info {
      border-bottom-color: rgba(255, 255, 255, 0.08);

      .logo-section {
        .logo-text { color: #d1d4dc; }
        .highlight { color: #00e5ff; }
      }

      .status-bar {
        .status-item {
          .label { color: #868993; }
          .value { color: #00e5ff; }
          .value.online { color: #52c41a; }
        }
      }
    }

    &::before {
      background:
        linear-gradient(135deg, rgba(24, 144, 255, 0.05) 0%, rgba(102, 126, 234, 0.05) 50%, rgba(135, 206, 250, 0.03) 100%),
        radial-gradient(circle at 20% 30%, rgba(24, 144, 255, 0.08) 0%, transparent 50%),
        radial-gradient(circle at 80% 70%, rgba(102, 126, 234, 0.08) 0%, transparent 50%);
    }

    &::after {
      background-image:
        linear-gradient(rgba(24, 144, 255, 0.05) 1px, transparent 1px),
        linear-gradient(90deg, rgba(24, 144, 255, 0.05) 1px, transparent 1px);
    }

    .analysis-header {
      .header-content {
        .title-section {
          .main-title {
            color: #d1d4dc;
          }

          .title-subtitle {
            color: #868993;
          }
        }
      }
    }

    ::v-deep .symbol-selector {
      .ant-select-selection {
        background-color: #2a2e39;
        border-color: #363c4e;
        color: #d1d4dc;

        &:hover {
          border-color: #1890ff;
        }
      }

      .ant-select-focused .ant-select-selection {
        border-color: #1890ff;
        box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.3);
      }

      .ant-select-arrow {
        color: #868993;
      }

      .ant-select-selection__placeholder {
        color: #868993;
      }
    }
  }

  .watchlist-section {
    background: #1e222d;
    border-color: #363c4e;

    .section-header {
      h3 {
        color: #d1d4dc;
      }
    }

    .watchlist-container {
      .watchlist-item {
        background: #2a2e39;
        border-color: #363c4e;

        &:hover {
          background: #363c4e;
          border-color: #1890ff;
        }

        .stock-info {
          .stock-symbol {
            color: #d1d4dc;
          }

          .stock-name {
            color: #868993;
          }
        }

        .stock-price {
          .price-value {
            color: #d1d4dc;
          }
        }
      }

      .empty-watchlist {
        ::v-deep .ant-empty-description {
          color: #868993;
        }
      }
    }
  }

}

/* 添加股票弹窗样式 */
.add-stock-modal-content {
  .market-tabs {
    margin-bottom: 16px;
  }

  .symbol-search-section {
    margin-bottom: 24px;
  }

  .search-results-section,
  .hot-symbols-section {
    margin-bottom: 24px;

    .section-title {
      font-size: 14px;
      font-weight: 600;
      color: #262626;
      margin-bottom: 12px;
      display: flex;
      align-items: center;
    }
  }

  .symbol-list {
    max-height: 200px;
    overflow-y: auto;
    border: 1px solid #e8e8e8;
    border-radius: 4px;

    .symbol-list-item {
      cursor: pointer;
      padding: 8px 12px;
      transition: background-color 0.3s;

      &:hover {
        background-color: #f5f5f5;
      }

      .symbol-item-content {
        display: flex;
        align-items: center;
        gap: 8px;

        .symbol-code {
          font-weight: 600;
          color: #262626;
          min-width: 80px;
        }

        .symbol-name {
          color: #595959;
          flex: 1;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }
      }
    }
  }

  .selected-symbol-section {
    margin-top: 16px;

    .selected-symbol-info {
      display: flex;
      align-items: center;
    }
  }

}

/* 暗黑主题下的弹窗样式 */
.ai-analysis-container.theme-dark,
:global(body.dark) .ai-analysis-container,
:global(body.realdark) .ai-analysis-container {
  .add-stock-modal-content {
    .search-results-section,
    .hot-symbols-section {
      .section-title {
        color: #d1d4dc;
      }
    }

    .symbol-list {
      border-color: #363c4e;
      background-color: #2a2e39;

      .symbol-list-item {
        &:hover {
          background-color: #363c4e;
        }

        .symbol-item-content {
          .symbol-code {
            color: #d1d4dc;
          }

          .symbol-name {
            color: #868993;
          }
        }
      }
    }
  }
}

</style>
