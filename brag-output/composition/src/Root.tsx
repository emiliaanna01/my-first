import { Composition } from "remotion";
import { RoundHouse, TOTAL } from "./Video";

export const RemotionRoot = () => (
  <Composition id="RoundHouse" component={RoundHouse} durationInFrames={TOTAL} fps={30} width={1920} height={1080} />
);
