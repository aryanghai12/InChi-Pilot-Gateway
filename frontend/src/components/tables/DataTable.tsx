import React from "react";
import styles from "./tables.module.css";
import { LoadingSpinner } from "../feedback/LoadingSpinner";
import { EmptyState } from "../feedback/EmptyState";

export interface Column<T> {
  key: string;
  header: string;
  render?: (row: T) => React.ReactNode;
}

interface DataTableProps<T> {
  columns: Column<T>[];
  data: T[];
  keyExtractor: (row: T) => string | number;
  isLoading?: boolean;
  emptyTitle?: string;
  emptyGuidance?: string;
  emptyAction?: React.ReactNode;
  className?: string;
}

export function DataTable<T>({
  columns,
  data,
  keyExtractor,
  isLoading = false,
  emptyTitle = "No records found",
  emptyGuidance = "There are no records to display matching the current criteria.",
  emptyAction,
  className = "",
}: DataTableProps<T>) {
  if (isLoading) {
    return <LoadingSpinner label="Loading records..." />;
  }

  if (data.length === 0) {
    return (
      <EmptyState
        title={emptyTitle}
        guidance={emptyGuidance}
        action={emptyAction}
      />
    );
  }

  return (
    <div className={`${styles.tableContainer} ${className}`}>
      <table className={styles.table}>
        <thead className={styles.thead}>
          <tr>
            {columns.map((col) => (
              <th key={col.key} scope="col" className={styles.th}>
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((row) => (
            <tr key={keyExtractor(row)} className={styles.tr}>
              {columns.map((col) => (
                <td key={col.key} className={styles.td}>
                  {col.render
                    ? col.render(row)
                    : (row as Record<string, unknown>)[col.key] != null
                    ? String((row as Record<string, unknown>)[col.key])
                    : "—"}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
