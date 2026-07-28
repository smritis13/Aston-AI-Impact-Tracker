import csv
import json
import pandas as pd
from io import BytesIO
from django.http import HttpResponse
from datetime import datetime
from io import StringIO

class ExportUtils:
    """
    Utility class for exporting data in different formats.
    """
    
    @staticmethod
    def export_to_csv(data, filename_prefix="export"):
        if not data:
            return HttpResponse("No data to export", status=400)
        
        # Use StringIO for CSV (text)
        output = StringIO()
        
        if data:
            fieldnames = data[0].keys()
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            for row in data:
                writer.writerow(row)
        
        # Get the CSV text
        csv_text = output.getvalue()
        output.close()
        
        # Now respond with bytes
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{filename_prefix}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        response.write(csv_text)  # It's okay because HttpResponse will handle it as text
        
        return response
    
    @staticmethod
    def export_to_excel(data, filename_prefix="export"):
        """
        Export data to Excel format.
        
        Args:
            data: List of dictionaries to export
            filename_prefix: Prefix for the filename
            
        Returns:
            HttpResponse with Excel file
        """
        if not data:
            return HttpResponse("No data to export", status=400)
            
        # Convert data to DataFrame
        df = pd.DataFrame(data)
        
        # Create a BytesIO buffer
        output = BytesIO()
        
        # Write Excel data to the buffer
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Sheet1')
        
        # Get the value of the buffer
        excel_data = output.getvalue()
        
        # Create the response
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename="{filename_prefix}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx"'
        response.write(excel_data)
        
        return response
    
    @staticmethod
    def export_to_json(data, filename_prefix="export"):
        """
        Export data to JSON format.
        
        Args:
            data: List of dictionaries to export
            filename_prefix: Prefix for the filename
            
        Returns:
            HttpResponse with JSON file
        """
        if not data:
            return HttpResponse("No data to export", status=400)
            
        # Convert data to JSON string
        json_data = json.dumps(data, indent=2)
        
        # Create the response
        response = HttpResponse(content_type='application/json')
        response['Content-Disposition'] = f'attachment; filename="{filename_prefix}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json"'
        response.write(json_data)
        
        return response 