import express from "express";
import axios from "axios";
import bodyParser from "body-parser";

const app = express();
const port = 3000;
const API_URL = "http://127.0.0.1:8000"

app.use(bodyParser.urlencoded({ extended: true }));
app.use(express.static("public"))

app.get("/", async(req, res) => { 
  try {
      const response = await axios.get(API_URL); 
      const data = (response.data); 
      console.log(data);
      res.render("index.ejs", {
        user: data.username,
        secret: data.secret
    });
  
    } catch (error) {
      console.error("Request failed:", error.message);
      res.render("index.ejs", {
        error: error.message,
      });
    }
});



app.listen(port, () => {
    console.log(`Server is running on port ${port}`);
  });
  