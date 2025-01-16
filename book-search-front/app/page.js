'use client';
import { useState, useEffect } from "react";
import styles from "./page.module.css";
import { IconButton, InputAdornment, TextField, Tooltip, Typography } from "@mui/material";
import SearchIcon from '@mui/icons-material/Search';
import axios from 'axios';
import LoadingPage from "./components/loading";
import ResultsPage from "./components/results";

const BACKEND_URL = 'https://booksearchbackend.onrender.com';
const BOOK_URL = BACKEND_URL+'/search-books';

const config = {
  headers: {
    "Access-Control-Allow-Origin": "https://book-search-frontend-vert.vercel.app",
    "Content-Type": "application/json"
  }
};

const indexConfig = {
  headers: {
    "Access-Control-Allow-Origin": "https://book-search-frontend-vert.vercel.app",
  }
};



export default function Home() {
  const [sentence, setSentence] = useState("");
  const [isOpen, setIsOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [respData, setRespData] = useState(null);
  const [errorData, setErrorData] = useState(null);

  useEffect(() => {
    //call index endpoint on startup to trigger backend start up during deployment
    axios.get(BACKEND_URL, indexConfig)
    .then(function(response) {
    }) //dont need to actually do anything with it, just sending the query is enough
    .catch(function(error) {
    })
  }, []); //run only on initial render

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
      setErrorData(null);
      setRespData(response.data);
      setIsLoading(false);
      setIsOpen(true);
    })
    .catch(function(error) {
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
        <Typography variant="body2">Powered by OpenLibrary and HuggingFace Zero Spaces</Typography>
        <Typography variant="body2">Kenneth Erickson</Typography>
      </footer>
    </div>
  );
}
