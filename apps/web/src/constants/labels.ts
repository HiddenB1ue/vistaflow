const WEB_LOCALES = {
  'zh-CN': {
    search: {
      greetingMorning: '风会经过站台',
      greetingNoon: '风会经过站台',
      greetingAfternoon: '风会经过站台',
      greetingEvening: '风会经过站台',
      headline: '',
      headlineAccent: '人会选择远方。',
      fromPrefix: '我想从',
      fromSuffix: '出发，前往',
      datePrefix: '，日期是',
      dateSuffix: '。',
      originPlaceholder: '出发地',
      destinationPlaceholder: '目的地',
      submitButton: '生成出行方案',
    },
    datePicker: {
      selectedDateEyebrow: '已选日期',
      prevMonthAriaLabel: '上一月',
      nextMonthAriaLabel: '下一月',
      monthSuffix: '月',
      yearSuffix: '年',
      closeLabel: '关闭日期选择器',
      weekdays: ['日', '一', '二', '三', '四', '五', '六'] as [string, string, string, string, string, string, string],
      presets: [
        { label: '今天', offsetDays: 0 },
        { label: '明天', offsetDays: 1 },
        { label: '一周后', offsetDays: 7 },
      ],
    },
    journey: {
      mapStatus: 'AI 实时路线推演',
      mapStatusIdle: 'AI 全局拓扑预览',
      routeListEyebrow: '方案列表',
      routeListTitle: (date: string) => `${date || '今天'} 出行方案`,
      routeListSubtitle: (count: number) => `共 ${count} 条结果，可按偏好筛选与排序。`,
      mapEyebrow: '路线地图',
      selectedRouteHint: (id: string) => `当前已选择方案：${id}`,
      noSelectionHint: '先在地图上浏览整体路径，再选择具体方案。',
      loading: '正在加载出行方案...',
      referencePrice: '参考起价',
      soldOut: '已售罄',
      ticketsAvailable: '余票充足',
      ticketsUnavailable: '余票暂不可用',
      ticketsNotQueried: '未查询余票',
      availableTicketsOnly: '只显示有余票',
      noSeatInfo: '暂无席别信息',
      disclaimerLine1: 'VistaFlow 仅提供行程规划参考，',
      disclaimerLine2: '实际购票请以前往官方渠道为准。',
      bookButton: '前往 12306 购票',
      viewStops: (count: number) => `查看 ${count} 个经停站`,
      stopDuration: (minutes: number) => `- 停留 ${minutes} 分钟`,
    },
    sort: {
      smart: '智能推荐',
      fastest: '耗时最短',
      cheapest: '价格最低',
    },
    navbar: {
      brand: 'VistaFlow',
      home: '首页',
      journeyPlan: '出行方案',
      filterButton: '出行偏好',
      themeToggle: '切换主题',
    },
    filter: {
      eyebrow: '偏好设置',
      title: '出行偏好',
      subtitle: '设置路线筛选与座位倾向，让方案列表与地图视图保持同样的选择逻辑。',
      directOnly: '仅看直达',
      directOnlyDesc: '只显示无需换乘的直达方案。',
      seatPreference: '座位偏好',
      business: '商务 / 特等',
      first: '一等座',
      second: '二等座',
      saveButton: '保存设置',
    },
    transition: {
      loading: '环境感知中…',
    },
    map: {
      noMapHint: 'AI 宏观拓扑预演',
    },
  },
} as const;

const WEB_LABEL_LOCALE = 'zh-CN' as const;
const WEB_LABELS = WEB_LOCALES[WEB_LABEL_LOCALE];

export const SEARCH_LABELS = WEB_LABELS.search;
export const DATE_PICKER_LABELS = WEB_LABELS.datePicker;
export const JOURNEY_LABELS = WEB_LABELS.journey;
export const SORT_LABELS = WEB_LABELS.sort;
export const NAVBAR_LABELS = WEB_LABELS.navbar;
export const FILTER_LABELS = WEB_LABELS.filter;
export const TRANSITION_LABELS = WEB_LABELS.transition;
