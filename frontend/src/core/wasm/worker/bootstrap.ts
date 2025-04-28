/* Copyright 2024 Marimo. All rights reserved. */
import { loadPyodide, type PyodideInterface } from "pyodide";
import { WasmFileSystem } from "./fs";
import { Logger } from "../../../utils/Logger";
import type { SerializedBridge, WasmController } from "./types";
import { invariant } from "../../../utils/invariant";
import type { UserConfig } from "@/core/config/config-schema";
import type { OperationMessage } from "@/core/kernel/messages";
import type { JsonString } from "@/utils/json/base64";
import { t } from "./tracer";

const MAKE_SNAPSHOT = false;
const LABDATA_TOKEN = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhcHBfcHJpdmlsZWdlcyI6ImZhbHNlIiwiYXBwX3VybCI6IjBnRHZ3YXYlMkJkWVZJYU9MM25xc2VXQyUyRnZ6SWF3NnJtaWQ5SzY4c083V01ZJTNEIiwiYXVkIjoiNm9hMTA5NW0yMHZnbDQyYm5iMDlkY2RiM24iLCJhdXRoX3RpbWUiOjE3NDU2NjUyMzksImNpdHkiOiIiLCJjb3VudHJ5IjoiRnJhbmNlIiwiZW1haWxzIjpbIkJyYWhpbS5zYWRraUBjYXJyaWVyLmNvbSJdLCJleHAiOjE3NDU3MDEyNDEsImZhbWlseV9uYW1lIjoiU0FES0kiLCJnaXZlbl9uYW1lIjoiQnJhaGltIiwiaHZhY3VzZXJuYW1lIjoiMDB1NzV4YTI3anBJeXpaM2Q0eDciLCJpYXQiOjE3NDU2NjUyNDEsImlkcCI6Imh0dHBzOi8vY29nbml0by1pZHAudXMtZWFzdC0yLmFtYXpvbmF3cy5jb20vdXMtZWFzdC0yXzVVRGhFVU9WTSIsImlzVmlld09ubHlBZG1pbiI6ZmFsc2UsImlzcyI6Imh0dHBzOi8vY29nbml0by1pZHAudXMtZWFzdC0yLmFtYXpvbmF3cy5jb20vdXMtZWFzdC0yXzVVRGhFVU9WTSIsIm5hbWUiOiJTQURLSSIsIm5iZiI6MTc0NTY2NTI0MSwibm9uY2UiOiI0MjI5OTM4YS0wYWE3LTRkODMtYjg0OS00MzhhZDg3OTAyZTYiLCJvaWQiOiJkYmU1NTcyYi01OTA0LTQzNzUtYWQwOS04MGI0NjQxNDliMDUiLCJwcml2aWxlZ2VzIjoiZmFsc2UiLCJzdGF0ZSI6IiIsInN1YiI6ImIxY2IyNWUwLTIwMzEtNzBkYi0zMmEzLWI3NDRiN2YyMThhOSIsInVzZXJJZCI6NzI5OSwidXNlcm5hbWUiOiJjYXJyaWVyb2t0YV8wMHU3NXhhMjdqcGl5enozZDR4NyIsInVzZXJ0eXBlIjoiQ2Fycmllck9rdGEiLCJ2ZXIiOiIyIiwidG9rZW5JZCI6IjE2NGU4YzcyLWRiYTctNDBiMS1hZDUzLTYxZWU0MzRlZGVkYSJ9.vJ7tm5fhar1Nnh5rknCIUv0MsjHHhxbTgyL1vb0QHi8"; // This should be replaced during build/deployment

// This class initializes the wasm environment
// We would like this initialization to be parallelizable
// however, there is some waterfall in the initialization process
// 1. Load Pyodide
// 2. Install marimo and its required dependencies
// 3. Install the dependencies from the notebook
//   3.a Install from pyodide supported wheels
//   3.b Install from micropip
// 4. Initialize the notebook

export class DefaultWasmController implements WasmController {
  protected pyodide: PyodideInterface | null = null;

  get requirePyodide() {
    invariant(this.pyodide, "Pyodide not loaded");
    return this.pyodide;
  }

  async bootstrap(opts: {
    version: string;
    pyodideVersion: string;
  }): Promise<PyodideInterface> {
    const pyodide = await this.loadPyodideAndPackages(opts);

    if (MAKE_SNAPSHOT) {
      const snapshot = pyodide.makeMemorySnapshot();
      Logger.log("Snapshot size (mb):", snapshot.byteLength / 1024 / 1024);
    }

    return pyodide;
  }

  private async loadPyodideAndPackages(opts: {
    version: string;
    pyodideVersion: string;
  }): Promise<PyodideInterface> {
    if (!loadPyodide) {
      throw new Error("loadPyodide is not defined");
    }
    // Load pyodide and packages
    const span = t.startSpan("loadPyodide");
    try {
      const pyodide = await loadPyodide({
        // Perf: These get loaded while pyodide is being bootstrapped
        packages: [
          "micropip",
          "marimo-base",
          "Markdown",
          "pymdown-extensions",
          "narwhals",
          "packaging",
        ],
        _makeSnapshot: MAKE_SNAPSHOT,
        lockFileURL: `https://wasm.marimo.app/pyodide-lock.json?v=${opts.version}&pyodide=${opts.pyodideVersion}`,
        // Without this, this fails in Firefox with
        // `Could not extract indexURL path from pyodide module`
        // This fixes for Firefox and does not break Chrome/others
        indexURL: `https://cdn.jsdelivr.net/pyodide/${opts.pyodideVersion}/full/`,
      });
      this.pyodide = pyodide;
      // load dependencies pandas, requests
      console.log("Dependencies installation (pandas, requests, httpx)...");
      await pyodide.loadPackage(["pandas", "requests", "httpx"]);
      // Load labdata_api manually after Pyodide initialization
      console.log("labdata_api installation...");
      const wheelUrl = "/pyodide/labdata_api-0.0.12-py3-none-any.whl";
      await pyodide.loadPackage(wheelUrl, {
        messageCallback: (msg) => console.log(msg),
        errorCallback: (err) => console.error(err)
      });

      // Initialize labdata token in Python environment
     try {await pyodide.runPythonAsync(`
        import os
        os.environ["LABDATA_TOKEN"] = "${LABDATA_TOKEN}"
        from labdata_api import Labdata
        #Initialize Labdata with token
        labdata = Labdata(token="${LABDATA_TOKEN}")
        # Test connection by fetching program
        #program = labdata.program
        print("✅ LABDATA_TOKEN configured!")
        import pandas as pd
        import requests
        print("✅ labdata_api, pandas and requests installed successfully!")
      `);
        } catch (error) {
        console.error("Failed to install labdata_api:", error);
        throw new Error(`Labdata API installation failed: ${error}`);
      }

      span.end("ok");
      return pyodide;
    } catch (error) {
      Logger.error("Failed to load Pyodide", error);
      throw error;
    }
  }

  async mountFilesystem(opts: { code: string; filename: string | null }) {
    const span = t.startSpan("mountFilesystem");
    // Set up the filesystem
    WasmFileSystem.createHomeDir(this.requirePyodide);
    WasmFileSystem.mountFS(this.requirePyodide);
    await WasmFileSystem.populateFilesToMemory(this.requirePyodide);
    span.end("ok");
    return WasmFileSystem.initNotebookCode({
      pyodide: this.requirePyodide,
      code: opts.code,
      filename: opts.filename,
    });
  }

  async startSession(opts: {
    queryParameters: Record<string, string | string[]>;
    code: string;
    filename: string | null;
    onMessage: (message: JsonString<OperationMessage>) => void;
    userConfig: UserConfig;
  }): Promise<SerializedBridge> {
    const { code, filename, onMessage, queryParameters, userConfig } = opts;
    // We pass down a messenger object to the code
    // This is used to have synchronous communication between the JS and Python code
    // Previously, we used a queue, but this would not properly flush the queue
    // during processing of a cell's code.
    //
    // This adds a messenger object to the global scope (import js; js.messenger.callback)
    self.messenger = {
      callback: onMessage,
    };
    self.query_params = queryParameters;
    self.user_config = userConfig;

    const span = t.startSpan("startSession.runPython");
    const nbFilename = filename || WasmFileSystem.NOTEBOOK_FILENAME;
    const [bridge, init, packages] = this.requirePyodide.runPython(
      `
      print("[py] Starting marimo...")
      import asyncio
      import js
      from marimo._pyodide.bootstrap import create_session, instantiate

      assert js.messenger, "messenger is not defined"
      assert js.query_params, "query_params is not defined"

      session, bridge = create_session(
        filename="${nbFilename}",
        query_params=js.query_params.to_py(),
        message_callback=js.messenger.callback,
        user_config=js.user_config.to_py(),
      )

      def init(auto_instantiate=True):
        instantiate(session, auto_instantiate)
        asyncio.create_task(session.start())

      # Find the packages to install
      with open("${nbFilename}", "r") as f:
        packages = session.find_packages(f.read())

      bridge, init, packages`,
    );
    span.end();

    const foundPackages = new Set<string>(packages.toJs());

    // Fire and forget:
    // Load notebook dependencies and instantiate the session
    // We don't want to wait for this to finish,
    // so we can show the initial code immediately giving
    // a sense of responsiveness.
    void this.loadNotebookDeps(code, foundPackages).then(() => {
      return init(userConfig.runtime.auto_instantiate);
    });

    return bridge;
  }

  private async loadNotebookDeps(code: string, foundPackages: Set<string>) {
    const pyodide = this.requirePyodide;

    if (code.includes("mo.sql")) {
      // We need pandas and duckdb for mo.sql
      code = `import pandas\n${code}`;
      code = `import duckdb\n${code}`;
      code = `import sqlglot\n${code}`;

      // Polars + SQL requires pyarrow, and installing
      // after notebook load does not work. As a heuristic,
      // if it appears that the notebook uses polars, add pyarrow.
      if (code.includes("polars")) {
        code = `import pyarrow\n${code}`;
      }
    }

    // Add:
    // 1. additional dependencies of marimo that are lazily loaded.
    // 2. pyodide-http, a patch to make basic http requests work in pyodide
    //
    // These packages are included with Pyodide, which is why we don't add them
    // to `foundPackages`:
    // https://pyodide.org/en/stable/usage/packages-in-pyodide.html
    code = `import docutils\n${code}`;
    code = `import pygments\n${code}`;
    code = `import jedi\n${code}`;
    code = `import pyodide_http\n${code}`;

    const imports = [...foundPackages];

    // Load from pyodide
    let loadSpan = t.startSpan("pyodide.loadPackage");
    await pyodide.loadPackagesFromImports(code, {
      errorCallback: Logger.error,
      messageCallback: Logger.log,
    });
    loadSpan.end();

    // Load from micropip
    loadSpan = t.startSpan("micropip.install");
    const missingPackages = imports.filter(
      (pkg) => !pyodide.loadedPackages[pkg],
    );
    if (missingPackages.length > 0) {
      await pyodide
        .runPythonAsync(`
        import micropip
        import sys
        # Filter out builtins
        missing = [p for p in ${JSON.stringify(missingPackages)} if p not in sys.modules]
        if len(missing) > 0:
          print("Loading from micropip:", missing)
          await micropip.install(missing)
      `)
        .catch((error) => {
          // Don't let micropip loading failures stop the notebook from loading
          Logger.error("Failed to load packages from micropip", error);
        });
    }
    loadSpan.end();
  }
}
