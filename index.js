import express from "express";
import axios from "axios";
import bodyParser from "body-parser";

const app = express();
const port = 3000;
const API_URL = "https://secrets-api.appbrewery.com/random";

app.use(bodyParser.urlencoded({ extended: true }));
app.use(express.static("public"))

app.get("/", async (req, res) => { // : Route path (e.g., 'users')
  try {
    const response = await axios.get(API_URL); // http://example.com/api: API endpoint URL
    const data = (response.data); // variable name (data) can be changed
    console.log(data);

    // Render the page and pass in the data
    res.render("index.ejs", {
        user: data.username,
        secret: data.secret
    }); // page: Template name (without extension)
  } catch (error) {
    console.error("Request failed:", error.message);
    res.render("index.ejs", {
      error: error.message,
    });
  }
});

// HINTS:
// 1. Import express and axios

// 2. Create an express app and set the port number.

// 3. Use the public folder for static files.

// 4. When the user goes to the home page it should render the index.ejs file.

// 5. Use axios to get a random secret and pass it to index.ejs to display the
// secret and the username of the secret.

// 6. Listen on your predefined port and start the server.

app.listen(port, () => {
    console.log(`Server is running on port ${port}`);
  });
  