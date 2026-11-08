import { exec } from "child_process";

export function Note({ html }: { html: string }) {
  return <div dangerouslySetInnerHTML={{ __html: html }} />;
}

export function run(name: string) {
  exec(`convert ${name} out.png`);
}
