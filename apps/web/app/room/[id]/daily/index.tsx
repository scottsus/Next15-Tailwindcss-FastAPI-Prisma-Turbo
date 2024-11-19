"use client";

import { DailyCall } from "@daily-co/daily-js";
import { DailyProvider } from "@daily-co/daily-react";
import { useState } from "react";

import Video from "./video";

export function DailyRoom() {
  const [callObject, setCallObject] = useState<DailyCall>();
  const [roomUrl, setRoomUrl] = useState("");

  return (
    <DailyProvider callObject={callObject} url={roomUrl}>
      <Video setCallObject={setCallObject} setRoomUrl={setRoomUrl} />
    </DailyProvider>
  );
}
