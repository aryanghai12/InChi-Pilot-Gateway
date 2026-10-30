import Link from "next/link";
import styles from "./not-found.module.css";

export default function NotFound() {
  return (
    <main className={styles.container}>
      <h1 className={styles.title}>404</h1>
      <h2 className={styles.subtitle}>Page Not Found</h2>
      <p className={styles.description}>
        The requested resource or page does not exist or has been moved.
      </p>
      <Link href="/dashboard" className={styles.actionButton}>
        Return to Dashboard
      </Link>
    </main>
  );
}
