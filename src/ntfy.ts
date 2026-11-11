export type Notification = { title: string; message: string; click: string };
export type Notify = (notification: Notification) => Promise<void>;

export function createNtfy({
  topic,
  server = "https://ntfy.sh",
  token,
}: {
  topic: string;
  server?: string;
  token?: string;
}): Notify {
  return async (notification) => {
    const response = await fetch(server, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({ topic, priority: 4, tags: ["tada"], ...notification }),
    });
    if (!response.ok) throw new Error(`ntfy responded ${response.status}`);
  };
}
