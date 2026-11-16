import { SearchIcon } from "./icons";

export function SearchBox({ go }: { go: () => void }) {
  return (
    <form>
      <input type="text" placeholder="Szukaj" />
      <button type="button" onClick={() => go()}>
        <SearchIcon />
      </button>
    </form>
  );
}
