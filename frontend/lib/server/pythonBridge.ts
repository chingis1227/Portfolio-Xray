import { existsSync } from "node:fs";
import path from "node:path";

export function resolvePythonExecutable(projectRoot: string) {
  const windowsVenvPython = path.join(projectRoot, ".venv", "Scripts", "python.exe");
  if (existsSync(windowsVenvPython)) {
    return windowsVenvPython;
  }

  const posixVenvPython = path.join(projectRoot, ".venv", "bin", "python");
  if (existsSync(posixVenvPython)) {
    return posixVenvPython;
  }

  return process.platform === "win32" ? "python.exe" : "python3";
}
