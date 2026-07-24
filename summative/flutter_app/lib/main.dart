import 'package:flutter/material.dart';
import 'dart:convert';
import 'package:http/http.dart' as http;

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Electricity Access Predictor',
      theme: ThemeData(primarySwatch: Colors.blue, useMaterial3: true),
      home: const PredictionPage(),
    );
  }
}

class PredictionPage extends StatefulWidget {
  const PredictionPage({super.key});

  @override
  State<PredictionPage> createState() => _PredictionPageState();
}

class _PredictionPageState extends State<PredictionPage> {
  int? _selectedYear;
  int? _selectedIncomeGroup;
  String? _selectedRegion;

  String _resultText = "";
  bool _isError = false;
  bool _isLoading = false;

  final String apiUrl =
      "https://linear-regression-summative-iu9s.onrender.com/predict";

  final List<int> _years = List.generate(41, (i) => 1990 + i); // 1990–2030

  final Map<int, String> _incomeGroups = {
    0: "Low income",
    1: "Lower middle income",
    2: "Upper middle income",
    3: "High income",
  };

  final List<String> _regions = [
    "East Asia & Pacific",
    "Europe & Central Asia",
    "Latin America & Caribbean",
    "Middle East & North Africa",
    "North America",
    "South Asia",
    "Sub-Saharan Africa",
  ];

  Future<void> _predict() async {
    if (_selectedYear == null || _selectedIncomeGroup == null || _selectedRegion == null) {
      setState(() {
        _resultText = "Please select a value for every field.";
        _isError = true;
      });
      return;
    }

    setState(() {
      _isLoading = true;
      _resultText = "";
      _isError = false;
    });

    try {
      final response = await http.post(
        Uri.parse(apiUrl),
        headers: {"Content-Type": "application/json"},
        body: jsonEncode({
          "year": _selectedYear,
          "income_group_num": _selectedIncomeGroup,
          "region": _selectedRegion,
        }),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        final prediction = data["predicted_electricity_access_percent"];
        setState(() {
          _resultText = "Predicted Electricity Access: ${prediction.toStringAsFixed(2)}%";
          _isError = false;
        });
      } else {
        final data = jsonDecode(response.body);
        setState(() {
          _resultText = _parseErrorMessage(data);
          _isError = true;
        });
      }
    } catch (e) {
      setState(() {
        _resultText = "Could not reach the server. Please check your connection.";
        _isError = true;
      });
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  // Turns FastAPI's raw validation error structure into a short, readable message
  String _parseErrorMessage(dynamic data) {
    final detail = data["detail"];
    if (detail is String) return "Error: $detail";
    if (detail is List && detail.isNotEmpty) {
      final firstError = detail[0];
      final field = (firstError["loc"] as List).last;
      final msg = firstError["msg"];
      return "Error: $field — $msg";
    }
    return "An unexpected error occurred.";
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("Electricity Access Predictor"),
        centerTitle: true,
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(20.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const SizedBox(height: 10),
              DropdownButtonFormField<int>(
                value: _selectedYear,
                decoration: const InputDecoration(
                  labelText: "Year",
                  border: OutlineInputBorder(),
                ),
                items: _years
                    .map((y) => DropdownMenuItem(value: y, child: Text(y.toString())))
                    .toList(),
                onChanged: (value) => setState(() => _selectedYear = value),
              ),
              const SizedBox(height: 16),
              DropdownButtonFormField<int>(
                value: _selectedIncomeGroup,
                decoration: const InputDecoration(
                  labelText: "Income Group",
                  border: OutlineInputBorder(),
                ),
                items: _incomeGroups.entries
                    .map((e) => DropdownMenuItem(value: e.key, child: Text(e.value)))
                    .toList(),
                onChanged: (value) => setState(() => _selectedIncomeGroup = value),
              ),
              const SizedBox(height: 16),
              DropdownButtonFormField<String>(
                value: _selectedRegion,
                decoration: const InputDecoration(
                  labelText: "Region",
                  border: OutlineInputBorder(),
                ),
                items: _regions
                    .map((r) => DropdownMenuItem(value: r, child: Text(r)))
                    .toList(),
                onChanged: (value) => setState(() => _selectedRegion = value),
              ),
              const SizedBox(height: 24),
              ElevatedButton(
                onPressed: _isLoading ? null : _predict,
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.green[600],
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(vertical: 16),
                ),
                child: _isLoading
                    ? const SizedBox(
                        height: 20,
                        width: 20,
                        child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                      )
                    : const Text("Predict", style: TextStyle(fontSize: 16)),
              ),
              const SizedBox(height: 24),
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: _isError ? Colors.red[50] : Colors.blue[50],
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(
                    color: _isError ? Colors.red[300]! : Colors.blue[300]!,
                    width: 1.5,
                  ),
                ),
                child: Text(
                  _resultText.isEmpty ? "Prediction will appear here." : _resultText,
                  style: TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.w600,
                    color: _isError ? Colors.red[700] : Colors.blue[900],
                  ),
                ),
              ),
              const SizedBox(height: 20),
            ],
          ),
        ),
      ),
    );
  }
}