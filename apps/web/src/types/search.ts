export interface SearchParams {
  origin: string;
  destination: string;
  date: string;
  transferCount: number;
  allowedTrainTypes: string[];
  excludedTrainTypes: string[];
  allowedTrains: string[];
  excludedTrains: string[];
  departureTimeStart: string;
  departureTimeEnd: string;
  arrivalDeadline: string;
  minTransferMinutes: number;
  maxTransferMinutes: string;
  allowedTransferStations: string[];
  excludedTransferStations: string[];
}

export interface SearchSuggestion {
  id: string;
  name: string;
  code: string;
  city: string;
}
