
export interface BackendSeatSchema {
  seat_type: string;
  status: string;
  price: number | null;
  available: boolean;
}

export interface BackendJourneySegment {
  train_code: string;
  from_station: string;
  to_station: string;
  departure_date: string;
  departure_time: string;
  arrival_date: string;
  arrival_time: string;
  duration_minutes: number;
  stops_count: number;
  seats: BackendSeatSchema[];
}

export interface BackendJourneyResult {
  id: string;
  is_direct: boolean;
  total_duration_minutes: number;
  departure_date: string;
  departure_time: string;
  arrival_date: string;
  arrival_time: string;
  min_price: number | null;
  segments: BackendJourneySegment[];
}

export interface BackendJourneySearchResponse {
  journeys: BackendJourneyResult[];
  total: number;
  date: string;
}

interface BackendStationGeoItem {
  name: string;
  longitude: number | null;
  latitude: number | null;
  found: boolean;
}

export interface BackendStationGeoResponse {
  items: BackendStationGeoItem[];
}
