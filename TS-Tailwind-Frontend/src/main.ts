import { App } from "./app.js";

const root = document.getElementById("app");
if (!root) throw new Error("Missing #app root element");

App(root);
