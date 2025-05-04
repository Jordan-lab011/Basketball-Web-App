import express from "express";
import axios from "axios";
import bodyParser from "body-parser";

const app = express();
const port = 3000;

app.use(bodyParser.urlencoded({ extended: true }));
app.use(express.static("public"))

app.get("/", (req, res) => { // : Route path (e.g., 'users')
  res.render("index.ejs")
});

app.listen(port, () => {
    console.log(`Server is running on port ${port}`);
  });
  