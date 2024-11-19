import { DailyRoom } from "./daily";

export default async function RoomPage() {
  return (
    <main className="flex size-full flex-1 flex-col items-center justify-center gap-y-6">
      <h1>Hello from Room</h1>
      <DailyRoom />
    </main>
  );
}
