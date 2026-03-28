import type { RouteList } from '@/types/route';
import { convertRouteListCoordinates } from '@/services/coordinateService';

const rawMockRoutes: RouteList = [
  {
    id: 'G1',
    trainNo: 'G1',
    type: '最优直达',
    origin: { name: '北京南', code: 'BJP', city: '北京', lng: 116.3783, lat: 39.8654 },
    destination: { name: '上海虹桥', code: 'SHH', city: '上海', lng: 121.3220, lat: 31.1945 },
    departureTime: '07:00',
    arrivalTime: '11:38',
    durationMinutes: 278,
    segs: [
      {
        no: 'G1',
        origin: { name: '北京南', code: 'BJP', city: '北京', lng: 116.3783, lat: 39.8654 },
        destination: { name: '上海虹桥', code: 'SHH', city: '上海', lng: 121.3220, lat: 31.1945 },
        departureTime: '07:00',
        arrivalTime: '11:38',
        stops: [],
        seats: [
          { type: 'business', label: '商务座', price: 1748, available: true, availabilityText: '仅剩 1 席' },
          { type: 'first', label: '一等座', price: 933, available: true },
          { type: 'second', label: '二等座', price: 553, available: true },
        ],
      },
    ],
    pathPoints: [
      { lng: 116.3783, lat: 39.8654 },
      { lng: 117.2008, lat: 39.0842 },
      { lng: 118.7969, lat: 37.4567 },
      { lng: 120.3856, lat: 36.0671 },
      { lng: 121.3220, lat: 31.1945 },
    ],
  },
  {
    id: 'G101',
    trainNo: 'G101',
    type: '最优直达',
    origin: { name: '北京南', code: 'BJP', city: '北京', lng: 116.3783, lat: 39.8654 },
    destination: { name: '上海虹桥', code: 'SHH', city: '上海', lng: 121.3220, lat: 31.1945 },
    departureTime: '08:00',
    arrivalTime: '12:28',
    durationMinutes: 268,
    segs: [
      {
        no: 'G101',
        origin: { name: '北京南', code: 'BJP', city: '北京', lng: 116.3783, lat: 39.8654 },
        destination: { name: '上海虹桥', code: 'SHH', city: '上海', lng: 121.3220, lat: 31.1945 },
        departureTime: '08:00',
        arrivalTime: '12:28',
        stops: [
          {
            station: { name: '济南西', code: 'JNX', city: '济南', lng: 116.8200, lat: 36.6757 },
            arrivalTime: '09:24',
            departureTime: '09:26',
            stopDuration: 2,
          },
          {
            station: { name: '南京南', code: 'NJN', city: '南京', lng: 118.7647, lat: 31.9571 },
            arrivalTime: '11:10',
            departureTime: '11:12',
            stopDuration: 2,
          },
        ],
        seats: [
          { type: 'business', label: '商务座', price: 1748, available: false },
          { type: 'first', label: '一等座', price: 933, available: true },
          { type: 'second', label: '二等座', price: 553, available: true },
        ],
      },
    ],
    pathPoints: [
      { lng: 116.3783, lat: 39.8654 },
      { lng: 116.8200, lat: 36.6757 },
      { lng: 118.7647, lat: 31.9571 },
      { lng: 121.3220, lat: 31.1945 },
    ],
  },
  {
    id: 'G103',
    trainNo: 'G103',
    type: '极速直达',
    origin: { name: '北京南', code: 'BJP', city: '北京', lng: 116.3783, lat: 39.8654 },
    destination: { name: '上海虹桥', code: 'SHH', city: '上海', lng: 121.3220, lat: 31.1945 },
    departureTime: '09:30',
    arrivalTime: '14:28',
    durationMinutes: 298,
    segs: [
      {
        no: 'G103',
        origin: { name: '北京南', code: 'BJP', city: '北京', lng: 116.3783, lat: 39.8654 },
        destination: { name: '上海虹桥', code: 'SHH', city: '上海', lng: 121.3220, lat: 31.1945 },
        departureTime: '09:30',
        arrivalTime: '14:28',
        stops: [
          {
            station: { name: '济南西', code: 'JNX', city: '济南', lng: 116.8200, lat: 36.6757 },
            arrivalTime: '10:52',
            departureTime: '10:54',
            stopDuration: 2,
          },
          {
            station: { name: '徐州东', code: 'XZD', city: '徐州', lng: 117.3089, lat: 34.2658 },
            arrivalTime: '12:08',
            departureTime: '12:10',
            stopDuration: 2,
          },
          {
            station: { name: '南京南', code: 'NJN', city: '南京', lng: 118.7647, lat: 31.9571 },
            arrivalTime: '13:10',
            departureTime: '13:12',
            stopDuration: 2,
          },
        ],
        seats: [
          { type: 'business', label: '商务座', price: 1748, available: true },
          { type: 'first', label: '一等座', price: 933, available: true },
          { type: 'second', label: '二等座', price: 553, available: false },
        ],
      },
    ],
    pathPoints: [
      { lng: 116.3783, lat: 39.8654 },
      { lng: 116.8200, lat: 36.6757 },
      { lng: 117.3089, lat: 34.2658 },
      { lng: 118.7647, lat: 31.9571 },
      { lng: 121.3220, lat: 31.1945 },
    ],
  },
  {
    id: 'G105-R',
    trainNo: 'G105 / G213',
    type: '省时中转',
    origin: { name: '北京南', code: 'BJP', city: '北京', lng: 116.3783, lat: 39.8654 },
    destination: { name: '上海虹桥', code: 'SHH', city: '上海', lng: 121.3220, lat: 31.1945 },
    departureTime: '09:15',
    arrivalTime: '15:40',
    durationMinutes: 385,
    segs: [
      {
        no: 'G105',
        origin: { name: '北京南', code: 'BJP', city: '北京', lng: 116.3783, lat: 39.8654 },
        destination: { name: '济南西', code: 'JNX', city: '济南', lng: 116.8200, lat: 36.6757 },
        departureTime: '09:15',
        arrivalTime: '11:05',
        stops: [],
        seats: [
          { type: 'second', label: '二等座', price: 215, available: true },
        ],
      },
      { transfer: '济南西 同站换乘 • 预留 45 分钟' },
      {
        no: 'G213',
        origin: { name: '济南西', code: 'JNX', city: '济南', lng: 116.8200, lat: 36.6757 },
        destination: { name: '上海虹桥', code: 'SHH', city: '上海', lng: 121.3220, lat: 31.1945 },
        departureTime: '11:50',
        arrivalTime: '15:40',
        stops: [
          {
            station: { name: '南京南', code: 'NJN', city: '南京', lng: 118.7647, lat: 31.9571 },
            arrivalTime: '13:45',
            departureTime: '13:47',
            stopDuration: 2,
          },
        ],
        seats: [
          { type: 'first', label: '一等座', price: 920, available: true },
          { type: 'second', label: '二等座', price: 580, available: true },
        ],
      },
    ],
    pathPoints: [
      { lng: 116.3783, lat: 39.8654 },
      { lng: 116.8200, lat: 36.6757 },
      { lng: 118.7647, lat: 31.9571 },
      { lng: 121.3220, lat: 31.1945 },
    ],
  },
  {
    id: 'G21',
    trainNo: 'G21',
    type: '傍晚直达',
    origin: { name: '北京南', code: 'BJP', city: '北京', lng: 116.3783, lat: 39.8654 },
    destination: { name: '上海虹桥', code: 'SHH', city: '上海', lng: 121.3220, lat: 31.1945 },
    departureTime: '17:00',
    arrivalTime: '21:40',
    durationMinutes: 280,
    segs: [
      {
        no: 'G21',
        origin: { name: '北京南', code: 'BJP', city: '北京', lng: 116.3783, lat: 39.8654 },
        destination: { name: '上海虹桥', code: 'SHH', city: '上海', lng: 121.3220, lat: 31.1945 },
        departureTime: '17:00',
        arrivalTime: '21:40',
        stops: [
          {
            station: { name: '南京南', code: 'NJN', city: '南京', lng: 118.7647, lat: 31.9571 },
            arrivalTime: '19:22',
            departureTime: '19:24',
            stopDuration: 2,
          },
        ],
        seats: [
          { type: 'business', label: '商务座', price: 2980, available: true },
          { type: 'first', label: '一等座', price: 933, available: true },
          { type: 'second', label: '二等座', price: 553, available: false },
        ],
      },
    ],
    pathPoints: [
      { lng: 116.3783, lat: 39.8654 },
      { lng: 118.7647, lat: 31.9571 },
      { lng: 121.3220, lat: 31.1945 },
    ],
  },
  {
    id: 'G107',
    trainNo: 'G107',
    type: '经济中转',
    origin: { name: '北京南', code: 'BJP', city: '北京', lng: 116.3783, lat: 39.8654 },
    destination: { name: '上海虹桥', code: 'SHH', city: '上海', lng: 121.3220, lat: 31.1945 },
    departureTime: '11:00',
    arrivalTime: '15:58',
    durationMinutes: 298,
    segs: [
      {
        no: 'G201',
        origin: { name: '北京南', code: 'BJP', city: '北京', lng: 116.3783, lat: 39.8654 },
        destination: { name: '徐州东', code: 'XZD', city: '徐州', lng: 117.3089, lat: 34.2658 },
        departureTime: '11:00',
        arrivalTime: '13:10',
        stops: [],
        seats: [
          { type: 'second', label: '二等座', price: 280, available: true },
        ],
      },
      { transfer: '徐州东 同站换乘 • 预留 30 分钟' },
      {
        no: 'G411',
        origin: { name: '徐州东', code: 'XZD', city: '徐州', lng: 117.3089, lat: 34.2658 },
        destination: { name: '上海虹桥', code: 'SHH', city: '上海', lng: 121.3220, lat: 31.1945 },
        departureTime: '13:40',
        arrivalTime: '15:58',
        stops: [
          {
            station: { name: '南京南', code: 'NJN', city: '南京', lng: 118.7647, lat: 31.9571 },
            arrivalTime: '14:48',
            departureTime: '14:50',
            stopDuration: 2,
          },
        ],
        seats: [
          { type: 'business', label: '商务座', price: 1748, available: true },
          { type: 'first', label: '一等座', price: 933, available: false },
          { type: 'second', label: '二等座', price: 400, available: true },
        ],
      },
    ],
    pathPoints: [
      { lng: 116.3783, lat: 39.8654 },
      { lng: 117.9583, lat: 38.3044 },
      { lng: 117.3089, lat: 34.2658 },
      { lng: 118.7647, lat: 31.9571 },
      { lng: 121.3220, lat: 31.1945 },
    ],
  },
];

export const mockRoutes: RouteList = convertRouteListCoordinates(rawMockRoutes);
