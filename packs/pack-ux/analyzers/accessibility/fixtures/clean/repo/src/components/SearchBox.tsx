import { useForm } from "react-hook-form";
import { SearchIcon } from "./icons";

export function SearchBox({ go, t }: { go: () => void; t: (k: string) => string }) {
  const { register } = useForm();
  return (
    <form>
      <label htmlFor="q">Szukaj</label>
      <input id="q" type="text" placeholder="np. rower" />
      <input type="hidden" name="source" value="header" />
      <label>
        Imię <input name="name" />
      </label>
      <input {...register("email")} />
      <button type="button" onClick={() => go()} aria-label="Szukaj">
        <SearchIcon />
      </button>
      <button type="submit">{t("search")}</button>
    </form>
  );
}
