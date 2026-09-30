import { useState } from "react";
import { Gamepad2 } from "lucide-react";
import type { Game } from "./types";

export default function GameArtwork({ game }: { game: Game }) {
  const [failed, setFailed] = useState(false);
  return game.image_url && !failed ? (
    <img
      className="game-cover"
      src={game.image_url}
      alt={`${game.name} artwork`}
      loading="lazy"
      onError={() => setFailed(true)}
    />
  ) : (
    <Gamepad2 size={100} strokeWidth={0.7} />
  );
}
