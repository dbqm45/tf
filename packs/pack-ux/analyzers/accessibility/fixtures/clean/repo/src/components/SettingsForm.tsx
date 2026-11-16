import { Field } from "./Field";

export function SettingsForm({ name, setName }: { name: string; setName: (v: string) => void }) {
  return (
    <Field label="Nazwa projektu">
      <input className="input" value={name} onChange={(e) => setName(e.target.value)} />
    </Field>
  );
}
