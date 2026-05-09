export const TILE_SERVER_URL =
  import.meta.env.VITE_TILE_SERVER_URL ?? 'http://127.0.0.1:8080';
const TILE_SERVER_STYLE =
  import.meta.env.VITE_TILE_SERVER_STYLE ?? 'basic';

/**
 * tileserver-gl 远程 style.json 绝对地址。
 * tileserver-gl 自带 CORS，浏览器可直接跨域请求，无需代理。
 */
export const REMOTE_STYLE_URL = `${TILE_SERVER_URL}/styles/${TILE_SERVER_STYLE}/style.json`;

/** 路线图层的配色，按主题切换 */
export const ROUTE_COLORS = {
  dawn: {
    line: '#e5c07b',
    glow: 'rgba(229,192,123,0.25)',
    station: '#e5c07b',
    stationBorder: 'rgba(229,192,123,0.5)',
  },
  dusk: {
    line: '#8b5cf6',
    glow: 'rgba(139,92,246,0.25)',
    station: '#8b5cf6',
    stationBorder: 'rgba(139,92,246,0.5)',
  },
} as const;
