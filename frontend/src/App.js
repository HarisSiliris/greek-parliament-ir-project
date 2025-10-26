// src/App.js
import React, { useState } from "react";
import {
  AppBar,
  Toolbar,
  Typography,
  Container,
  TextField,
  Button,
  Grid,
  Card,
  CardContent,
  Pagination,
  Stack,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from "@mui/material";
import { LocalizationProvider, DatePicker } from "@mui/x-date-pickers";
import { AdapterDateFns } from "@mui/x-date-pickers/AdapterDateFns";
import axios from "axios";
import format from "date-fns/format";
import { el } from "date-fns/locale";

function App() {
  const [query, setQuery] = useState("");
  const [fromDate, setFromDate] = useState(null);
  const [toDate, setToDate] = useState(null);
  const [results, setResults] = useState([]);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [selectedSpeech, setSelectedSpeech] = useState(null);
  const [modalOpen, setModalOpen] = useState(false);

  const size = 10; // Αποτελέσματα ανά σελίδα

  // --- Modal functions ---
  const handleOpenModal = (speech) => {
    setSelectedSpeech(speech);
    setModalOpen(true);
  };

  const handleCloseModal = () => {
    setSelectedSpeech(null);
    setModalOpen(false);
  };

  // --- Search function ---
  const handleSearch = async (newPage = 1) => {
    try {
      const params = {
        q: query || undefined,
        from_date: fromDate ? format(fromDate, "dd/MM/yyyy") : undefined,
        to_date: toDate ? format(toDate, "dd/MM/yyyy") : undefined,
        page: newPage,
        size: size,
      };

      const res = await axios.get("http://localhost:8000/search", { params });

      setResults(res.data.results);
      setPage(res.data.page);
      setTotalPages(res.data.total_pages);
    } catch (err) {
      console.error("Error fetching data:", err);
    }
  };

  const handlePageChange = (event, value) => {
    setPage(value);
    handleSearch(value);
  };

  return (
    <div>
      <AppBar position="static" sx={{ backgroundColor: "#0B5394" }}>
        <Toolbar>
          <Typography variant="h6">Greek Parliament Speeches</Typography>
        </Toolbar>
      </AppBar>

      <Container sx={{ mt: 4 }}>
        <LocalizationProvider dateAdapter={AdapterDateFns} adapterLocale={el}>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} sm={4}>
              <TextField
                fullWidth
                label="Search"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
              />
            </Grid>
            <Grid item xs={6} sm={3}>
              <DatePicker
                label="From Date"
                value={fromDate}
                onChange={(newValue) => {
                  setFromDate(newValue);
                  if (toDate && newValue && newValue > toDate) setToDate(null);
                }}
                inputFormat="dd/MM/yyyy"
                renderInput={(params) => <TextField fullWidth {...params} />}
              />
            </Grid>
            <Grid item xs={6} sm={3}>
              <DatePicker
                label="To Date"
                value={toDate}
                onChange={(newValue) => setToDate(newValue)}
                minDate={fromDate || undefined}
                disabled={!fromDate}
                inputFormat="dd/MM/yyyy"
                renderInput={(params) => <TextField fullWidth {...params} />}
              />
            </Grid>
            <Grid item xs={12} sm={2}>
              <Button
                fullWidth
                variant="contained"
                color="primary"
                onClick={() => handleSearch(1)}
              >
                Search
              </Button>
            </Grid>
          </Grid>
        </LocalizationProvider>

        <Grid container spacing={2} sx={{ mt: 4 }}>
          {results.length === 0 && (
            <Typography variant="body1">No results yet.</Typography>
          )}
          {results.map((speech, idx) => (
            <Grid item xs={12} key={idx}>
              <Card
                onClick={() => handleOpenModal(speech)}
                sx={{ cursor: "pointer" }}
              >
                <CardContent>
                  <Typography variant="h6">{speech.member_name}</Typography>
                  <Typography variant="subtitle2">{speech.party}</Typography>
                  <Typography variant="caption">{speech.date}</Typography>
                  <Typography
                    variant="body2"
                    sx={{
                      mt: 1,
                      display: "-webkit-box",
                      WebkitLineClamp: 3,
                      WebkitBoxOrient: "vertical",
                      overflow: "hidden",
                    }}
                  >
                    {speech.speech}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>

        {totalPages > 1 && (
          <Stack alignItems="center" sx={{ mt: 3 }}>
            <Pagination
              count={totalPages}
              page={page}
              onChange={handlePageChange}
              color="primary"
            />
          </Stack>
        )}

        {/* --- Modal για πλήρη ομιλία --- */}
        <Dialog open={modalOpen} onClose={handleCloseModal} fullWidth maxWidth="md">
          <DialogTitle>
            {selectedSpeech?.member_name} - {selectedSpeech?.party}
          </DialogTitle>
          <DialogContent dividers>
            <Typography variant="caption">{selectedSpeech?.date}</Typography>
            <Typography variant="body1" sx={{ mt: 2 }}>
              {selectedSpeech?.speech}
            </Typography>
          </DialogContent>
          <DialogActions>
            <Button onClick={handleCloseModal}>Close</Button>
          </DialogActions>
        </Dialog>
      </Container>
    </div>
  );
}

export default App;
