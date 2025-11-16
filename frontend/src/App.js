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
  MenuItem,
  Select,
  InputLabel,
  FormControl,
  Chip,
  Box,
} from "@mui/material";
import { LocalizationProvider, DatePicker } from "@mui/x-date-pickers";
import { AdapterDateFns } from "@mui/x-date-pickers/AdapterDateFns";
import Autocomplete from "@mui/material/Autocomplete";
import axios from "axios";
import format from "date-fns/format";
import { el } from "date-fns/locale";

function App() {
  const [currentPage, setCurrentPage] = useState("search"); // "search" or "trends"

  // --- Search state ---
  const [query, setQuery] = useState("");
  const [fromDate, setFromDate] = useState(null);
  const [toDate, setToDate] = useState(null);
  const [results, setResults] = useState([]);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [selectedSpeech, setSelectedSpeech] = useState(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [speechKeywords, setSpeechKeywords] = useState([]);

  // --- Trends state ---
  const [entityType, setEntityType] = useState("party");
  const [entityName, setEntityName] = useState("");
  const [trends, setTrends] = useState([]);
  // --- Autocomplete state ---
  const [autocompleteOptions, setAutocompleteOptions] = useState([]);

  const fetchAutocompleteOptions = async (entityType, query) => {
    if (!query || query.length < 2) {
      setAutocompleteOptions([]);
      return;
    }

    try {
      const res = await axios.get("http://localhost:8000/autocomplete", {
        params: { entity_type: entityType, q: query },
      });

      // The backend now returns a plain list — just use it safely
      const data = Array.isArray(res.data) ? res.data : [];
      setAutocompleteOptions(data);
    } catch (err) {
      console.error("Error fetching autocomplete:", err);
      setAutocompleteOptions([]);
    }
  };

  const size = 10; // Results per page

  // --- Modal functions ---
  const handleOpenModal = async (speech) => {
    setSelectedSpeech(speech);
    setModalOpen(true);
    setSpeechKeywords([]);

    // Προσπάθα να πάρεις το πραγματικό ES id — μπορεί να είναι `id` ή `_id`
    const speechId = speech?.id || speech?._id;

    if (!speechId) {
      console.warn("No speech id available to fetch keywords.");
      return;
    }

    try {
      const res = await axios.get(`http://localhost:8000/keywords/speech/${encodeURIComponent(speechId)}`);
      if (res.data.keywords) {
        // keywords στο backend είναι [(kw,score), ...] — παίρνουμε μόνο τις λέξεις
        setSpeechKeywords(res.data.keywords.map((k) => Array.isArray(k) ? k[0] : k));
      }
    } catch (err) {
      console.warn("No keywords found for this speech.", err);
    }
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

  // --- Fetch keyword trends ---
  const handleFetchTrends = async () => {
    if (!entityName.trim()) return;

    try {
      const res = await axios.get("http://localhost:8000/keywords/trends", {
        params: { entity_type: entityType, name: entityName },
      });
      if (res.data.error || res.data.message) {
        setTrends([]);
        alert(res.data.error || res.data.message);
        return;
      }
      setTrends(res.data);
    } catch (err) {
      console.error("Error fetching trends:", err);
    }
  };

  return (
    <div>
      <AppBar position="static" sx={{ backgroundColor: "#0B5394" }}>
        <Toolbar>
          <Typography variant="h6" sx={{ flexGrow: 1 }}>
            Greek Parliament Speeches
          </Typography>
          <Button color="inherit" onClick={() => setCurrentPage("search")}>
            Search
          </Button>
          <Button color="inherit" onClick={() => setCurrentPage("trends")}>
            Keyword Trends
          </Button>
        </Toolbar>
      </AppBar>

      <Container sx={{ mt: 4 }}>
        {/* 🔹 Keyword Trends Section */}
        {currentPage === "trends" && (
          <>
            <Typography variant="h6" sx={{ mb: 2 }}>
              Keyword Trends
            </Typography>

            <Grid container spacing={2} alignItems="center">
              {/* Dropdown */}
              <Grid item xs={12} sm={3}>
                <FormControl fullWidth>
                  <InputLabel id="entity-type-label">Type</InputLabel>
                  <Select
                    labelId="entity-type-label"
                    value={entityType}
                    label="Type"
                    onChange={(e) => setEntityType(e.target.value)}
                  >
                    <MenuItem value="party">Party</MenuItem>
                    <MenuItem value="member">Member</MenuItem>
                  </Select>
                </FormControl>
              </Grid>

              {/* Autocomplete */}
              <Grid item xs={12} sm={6}>
                <Autocomplete
                  freeSolo
                  fullWidth
                  options={autocompleteOptions}
                  inputValue={entityName}
                  onInputChange={(event, newValue) => {
                    setEntityName(newValue);
                    fetchAutocompleteOptions(entityType, newValue);
                  }}
                  renderInput={(params) => (
                    <TextField
                      {...params}
                      fullWidth
                      label={entityType === "party" ? "Party Name" : "Member Name"}
                      variant="outlined"
                      InputProps={{
                        ...params.InputProps,
                        sx: {
                          transition: "width 0.2s ease",
                          width: `${Math.min(300 + entityName.length * 8, 450)}px`, // 🔹 dynamic width
                          maxWidth: "100%", // 🔹 prevent overflow
                        },
                      }}
                    />
                  )}
                  sx={{
                    "& .MuiInputBase-root": { minHeight: "56px" },
                  }}
                />
              </Grid>

              {/* Button */}
              <Grid item xs={12} sm={3}>
                <Button
                  fullWidth
                  variant="contained"
                  onClick={handleFetchTrends}
                  sx={{ height: "56px" }}
                >
                  Show Trends
                </Button>
              </Grid>
            </Grid>

            {/* Results */}
            {trends.length > 0 && (
              <Box sx={{ mt: 3 }}>
                {trends.map((item) => (
                  <Card key={item.year} sx={{ mt: 1 }}>
                    <CardContent>
                      <Typography variant="h6">{item.year}</Typography>
                      {item.keywords.map((kw, i) => (
                        <Chip key={i} label={kw} sx={{ mr: 0.5, mt: 0.5 }} />
                      ))}
                    </CardContent>
                  </Card>
                ))}
              </Box>
            )}
          </>
        )}

        {/* 🔹 Search Section */}
        {currentPage === "search" && (
          <>
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
              {results.length === 0 && <Typography>No results yet.</Typography>}
              {results.map((speech) => (
                <Grid item xs={12} key={speech.id || speech._id || JSON.stringify(speech)}>
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
                      {/* ✅ Εδώ προσθέτουμε τα top 5 keywords */}
                      {speech.keywords && speech.keywords.length > 0 && (
                        <Box sx={{ mt: 1 }}>
                          {speechKeywords.slice(0, 5).map((kw, i) => (
                            <Chip key={i} label={kw} size="small" sx={{ mr: 0.5, mt: 0.5 }} />
                          ))}
                        </Box>
                      )}
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
          </>
        )}

        {/* --- Modal for full speech --- */}
        <Dialog open={modalOpen} onClose={handleCloseModal} fullWidth maxWidth="md">
          <DialogTitle>
            {selectedSpeech?.member_name} - {selectedSpeech?.party}
          </DialogTitle>
          <DialogContent dividers>
            <Typography variant="caption">{selectedSpeech?.date}</Typography>

            {speechKeywords.length > 0 && (
              <Box sx={{ my: 2 }}>
                <Typography variant="subtitle2">Top Keywords:</Typography>
                {speechKeywords.map((kw, i) => (
                  <Chip key={i} label={kw} sx={{ mr: 0.5, mt: 0.5 }} />
                ))}
              </Box>
            )}

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
