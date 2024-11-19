"use client";

import { DailyCall } from "@daily-co/daily-js";
import {
  DailyAudio,
  DailyVideo,
  useCallObject,
  useLocalSessionId,
} from "@daily-co/daily-react";
import { useEffect } from "react";

import { createRoom, dialClone } from "./api";
import { EndResponseButton } from "./endResponse";

export default function Video({
  setCallObject,
  setRoomUrl,
}: {
  setCallObject: React.Dispatch<React.SetStateAction<DailyCall | undefined>>;
  setRoomUrl: React.Dispatch<React.SetStateAction<string>>;
}) {
  const localSessionId = useLocalSessionId();
  const callObject = useCallObject({});

  useEffect(() => {
    if (!callObject) {
      console.log("Empty callObject");
      return;
    }

    callObject
      .startCamera()
      .then(() => createRoom())
      .then(({ url }) => {
        console.log("Joining", url);

        callObject.join({ url: url });
        setCallObject(callObject);
        setRoomUrl(url);

        console.log("Successfully set everything!");

        return url;
      })
      .then((url) => {
        dialClone({ roomUrl: url });
      });
  }, [callObject]);

  return (
    <div className="rounded-lg bg-red-500">
      <DailyAudio />
      <DailyVideo
        style={{
          width: "100%",
          height: "100%",
          overflow: "hidden",
          borderRadius: "20px",
        }}
        sessionId={localSessionId}
        automirror
        fit="cover"
        type={"video"}
      />
      <EndResponseButton />
    </div>
  );
}
