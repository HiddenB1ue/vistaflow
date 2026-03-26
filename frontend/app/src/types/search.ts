export interface SearchParams {
  origin: string;
  destination: string;
  date: string;
}

export interface SearchSuggestion {
  id: string;
  name: string;
  code: string;
  city: string;
}
