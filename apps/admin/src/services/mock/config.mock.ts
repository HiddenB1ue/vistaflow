import type { ApiCredential, GlobalToggle } from '@/types/config';

export const MOCK_CREDENTIALS: ApiCredential[] = [
  {
    id: 'cred-1',
    name: '地图服务接口',
    description: '用于经纬度解析、路线距离计算 · 高德地图 API',
    health: 'healthy',
    maskedKey: 'sk_live_8f92••••••••••••••3a1c',
    quotaInfo: '100,000 / month · 已用 75%',
  },
  {
    id: 'cred-2',
    name: '票务查询代理凭证',
    description: '第三方代理 Token · 当前值来自数据库覆盖',
    health: 'expired',
    maskedKey: 'eyJhbGciOiJIUzI1...',
    expiryWarning: '签发于 2025-12-01 · 已过期 119 天',
  },
];

export const MOCK_TOGGLES: GlobalToggle[] = [
  {
    id: 'auto-retry',
    label: '开启自动重试',
    description: '任务失败后按配置自动重试，最多 3 次。',
    enabled: true,
  },
  {
    id: 'preview-write',
    label: '落库前强制预览',
    description: '所有补全类任务执行后需先经过人工确认才可落库。',
    enabled: true,
  },
  {
    id: 'email-alerts',
    label: '告警邮件通知',
    description: '系统异常时发送邮件至 admin@vistaflow.app。',
    enabled: false,
  },
  {
    id: 'maintenance',
    label: '维护模式',
    description: '开启后对外接口返回 503，后台任务仍可继续运行。',
    enabled: false,
  },
];
