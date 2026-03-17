// this starts the application by finding the root element and calling the App function

/* 
Only Modify this file to:
1) Changing how the app is started
2) Adding global error handling 
3) Adding performance measurement
*/

import { App } from "./App.js";
import { fetchCurrentUser } from "./shared/auth.js";

const root = document.getElementById("app");
if (!root) throw new Error("Missing #app root element");

async function bootstrap() {
  try {
    const currentUser = await fetchCurrentUser();
    App(root!, currentUser);
  } catch (error) {
    console.error("Failed to bootstrap app", error);
    App(root!, null);
  }
}

bootstrap();
