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
  final TextEditingController _yearController = TextEditingController();
  final TextEditingController _incomeController = TextEditingController();
  final TextEditingController _regionController = TextEditingController();

  String _resultText = "";
  bool _isLoading = false;

  final String apiUrl =
      "https://linear-regression-summative-iu9s.onrender.com/predict";

  Future<void> _predict() async {
    // basic check: make sure nothing is empty before calling the API
    if (_yearController.text.isEmpty ||
        _incomeController.text.isEmpty ||
        _regionController.text.isEmpty) {
      setState(() {
        _resultText = "Error: please fill in all fields.";
      });
      return;
    }

    setState(() {
      _isLoading = true;
      _resultText = "";
    });

    try {
      final response = await http.post(
        Uri.parse(apiUrl),
        headers: {"Content-Type": "application/json"},
        body: jsonEncode({
          "year": int.parse(_yearController.text),
          "income_group_num": int.parse(_incomeController.text),
          "region": _regionController.text,
        }),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        final prediction = data["predicted_electricity_access_percent"];
        setState(() {
          _resultText =
              "Predicted Electricity Access: ${prediction.toStringAsFixed(2)}%";
        });
      } else {
        final data = jsonDecode(response.body);
        setState(() {
          _resultText = "Error: ${data["detail"]}";
        });
      }
    } catch (e) {
      setState(() {
        _resultText = "Error: could not reach the server. $e";
      });
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("Electricity Access Predictor"),
        centerTitle: true,
      ),
      body: Padding(
        padding: const EdgeInsets.all(20.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const SizedBox(height: 10),
            TextField(
              controller: _yearController,
              keyboardType: TextInputType.number,
              decoration: const InputDecoration(
                labelText: "Year (1990–2030)",
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 16),
            TextField(
              controller: _incomeController,
              keyboardType: TextInputType.number,
              decoration: const InputDecoration(
                labelText: "Income Group (0=Low, 1=Lower-mid, 2=Upper-mid, 3=High)",
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 16),
            TextField(
              controller: _regionController,
              decoration: const InputDecoration(
                labelText: "Region (e.g. Sub-Saharan Africa)",
                border: OutlineInputBorder(),
              ),
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
                      child: CircularProgressIndicator(
                        strokeWidth: 2,
                        color: Colors.white,
                      ),
                    )
                  : const Text("Predict", style: TextStyle(fontSize: 16)),
            ),
            const SizedBox(height: 24),
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Colors.blue[50],
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: Colors.blue[300]!, width: 1.5),
              ),
              child: Text(
                _resultText.isEmpty
                    ? "Prediction will appear here."
                    : _resultText,
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.w600,
                  color: _resultText.startsWith("Error")
                      ? Colors.red[700]
                      : Colors.blue[900],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}