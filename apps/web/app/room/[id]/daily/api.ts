"use server";

export async function createRoom() {
  const dailyApiKey = process.env.NEXT_PUBLIC_DAILY_API_KEY;
  if (!dailyApiKey) {
    throw new Error("NEXT_PUBLIC_DAILY_API_KEY not set");
  }

  const body = JSON.stringify({ properties: { enable_recording: "cloud" } });
  const res = await fetch("https://api.daily.co/v1/rooms", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${dailyApiKey}`,
    },
    body,
  });

  const roomData = await res.json();

  console.log("RoomURL:", roomData.url);

  return roomData;
}

export async function dialClone({ roomUrl }: { roomUrl: string }) {
  const cloneEndpoint = process.env.NEXT_PUBLIC_CLONE_ENDPOINT;
  if (!cloneEndpoint) {
    throw new Error("NEXT_PUBLIC_CLONE_ENDPOINT not set");
  }

  try {
    const res = await fetch(`${cloneEndpoint}/clone`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        room_url: roomUrl,
      }),
    });

    if (!res.ok) {
      throw new Error("non-200 status code");
    }
    return true;
  } catch (err: any) {
    console.error("dialClone:", err);
    return false;
  }
}