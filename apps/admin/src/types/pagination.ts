/**
 * Generic paginated response structure.
 * Used by all paginated API endpoints.
 */
export interface PaginatedResponse<T> {
  items: T[];
  page: number;
  pageSize: number;
  total: number;
  totalPages: number;
}

/**
 * Query parameters for tasks list pagination.
 */
export interface TaskListQuery {
  page: number;
  pageSize: number;
  keyword: string;
  status: string;
}

/**
 * Query parameters for system logs pagination.
 */
export interface SystemLogsQuery {
  page: number;
  pageSize: number;
  keyword: string;
  severity: string;
}

/**
 * Query parameters for task runs pagination.
 */
export interface TaskRunsQuery {
  page: number;
  pageSize: number;
}

/**
 * Query parameters for task run logs pagination.
 */
export interface TaskRunLogsQuery {
  page: number;
  pageSize: number;
}
