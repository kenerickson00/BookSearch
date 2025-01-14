'use client';
import { useState } from "react";
import styles from "./page.module.css";
import { IconButton, InputAdornment, TextField, Tooltip, Typography } from "@mui/material";
import SearchIcon from '@mui/icons-material/Search';
import axios from 'axios';
import LoadingPage from "./components/loading";
import ResultsPage from "./components/results";

const BACKEND_URL = 'http://127.0.0.1:8000/';
const BOOK_URL = 'http://127.0.0.1:8000/search-books';

const config1 = {
  headers: {
    "Access-Control-Allow-Origin": "*"
  }
};

const getIndex = () => {
  axios.get(BACKEND_URL, config1)
    .then(function(response) {
      console.log("Success: "+response);
    })
    .catch(function(error) {
      console.log('Error: '+error)
    })
};

const config = {
  headers: {
    "Access-Control-Allow-Origin": "*",
    "Content-Type": "application/json"
  }
};


export default function Home() {
  const [sentence, setSentence] = useState("");
  const [isOpen, setIsOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [respData, setRespData] = useState(null);
  const [errorData, setErrorData] = useState(null);

  const changeSentence = (event) => {
    setSentence(event.target.value);
  };

  const bookSearch = () => {
    setIsLoading(true);
    setIsOpen(false);
    const body = {
      'sentence': sentence
    };

    axios.post(BOOK_URL, body, config)
    .then(function(response) {
      console.log(response);
      setErrorData(null);
      setRespData(response.data);
      setIsLoading(false);
      setIsOpen(true);
    })
    .catch(function(error) {
      console.log(error.response.data.detail);
      setErrorData(error.response.data.detail);
      setRespData(null);
      setIsLoading(false);
      setIsOpen(true);
    })
  }

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center'
        }}>
          <Typography variant='h2'>Book Search</Typography>
          <Typography variant="body2">Find new books using the power of AI!</Typography>
        </div>
      </header>
      <LoadingPage isOpen={isLoading} />
      <ResultsPage 
        isOpen={isOpen}
        respData={respData}
        errorData={errorData}
        close={() => setIsOpen(false)}
      />
      <main className={styles.main}>
        <TextField variant="outlined" color="success" focused 
          label="Ask a question to get started" value={sentence} onChange={changeSentence}
          style={{
            width: '35vw',
            paddingBottom: '15vh',
          }}
          slotProps={{
            input: {
              endAdornment: <InputAdornment position="end">
                <Tooltip title="Start Search" placement="right">
                  <IconButton
                    color="success"
                    onClick={bookSearch}>
                    <SearchIcon fontSize="large"/>
                  </IconButton>
                </Tooltip>
              </InputAdornment>,
            }
          }}
        />
      </main>
      <footer className={styles.footer}>
        <Typography variant="body2">Powered by OpenLibrary and Mistral-7b</Typography>
        <Typography variant="body2">Kenneth Erickson</Typography>
      </footer>
    </div>
  );
}
