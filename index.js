import express from "express";
import axios from "axios";
import bodyParser from "body-parser";

//<script async src="https://cse.google.com/cse.js?cx=97288c4fc65664c6f">
//</script>
//<div class="gcse-search"></div>
//https://www.googleapis.com/customsearch/v1?key=AIzaSyCtM6oJIUAi8dK9HcYm5-AV1KIRAYHh8gw&cx=97288c4fc65664c6f&q=Kyrie%20Irving&num=1&dateRestrict=d[1]&imgSize=xlarge
const app = express();
const port = 3000;
const NBA_API_URL = "http://127.0.0.1:8000"
const google_api_key = "AIzaSyCtM6oJIUAi8dK9HcYm5-AV1KIRAYHh8gw"
const cx = "97288c4fc65664c6f"
 
app.use(bodyParser.urlencoded({ extended: true }));
app.use(express.static("public"))

app.get("/", async(req, res) => { 
      const response = await axios.get(`${NBA_API_URL}/player-of-the-day`); 
      const data = (response.data); 
      const player = data.player_of_the_day.Player;
      console.log(data);

      // Fetching player image using Google Custom Search API
      const searchResponse = await axios.get(`https://www.googleapis.com/customsearch/v1?key=AIzaSyCtM6oJIUAi8dK9HcYm5-AV1KIRAYHh8gw&cx=97288c4fc65664c6f&q=${player}&num=1&dateRestrict=d[1]&imgSize=xlarge&searchType=image`);
      const searchData = searchResponse.data;
      const playerImage = searchData.items[0].link;
      console.log(playerImage);
      res.render("index.ejs", {
        date: data.date,
        playerOfTheDay: data.player_of_the_day,
        team: data.Team,
        pts: data.Points,
        rebs: data.Rebounds,
        asts: data.Assists,
        opp: data.Opponent,
        imageSrc: playerImage,
    });
});



app.listen(port, () => {
    console.log(`Server is running on port ${port}`);
  });
  