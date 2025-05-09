import pandas as pd
import sys
import io
import locale
import numpy as np
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import time
import os

# Cấu hình encoding cho đầu ra terminal
sys.stdout.reconfigure(encoding='utf-8')  # Python 3.7+ syntax

# Thử thiết lập locale cho hệ thống
try:
    locale.setlocale(locale.LC_ALL, 'vi_VN.UTF-8')  # Với Linux/Mac
except:
    try:
        locale.setlocale(locale.LC_ALL, 'Vietnamese_Vietnam.1258')  # Với Windows
    except:
        pass  # Bỏ qua nếu không thể thiết lập locale

def load_data(file_path):
    """
    Đọc dữ liệu từ file CSV với cải tiến tốc độ
    """
    # Kiểm tra xem có tệp cache chưa
    cache_file = file_path + '.pickle'
    if os.path.exists(cache_file):
        try:
            start_time = time.time()
            data = pd.read_pickle(cache_file)
            print(f"Dữ liệu đã được tải từ cache trong {time.time() - start_time:.2f} giây")
            print(f"Dữ liệu gồm {data.shape[0]} bệnh và {data.shape[1]-1} triệu chứng")
            return data
        except Exception as e:
            print(f"Lỗi khi đọc cache: {e}")
    
    # Nếu không có cache hoặc lỗi, tải từ CSV
    start_time = time.time()
    encodings = ['utf-8', 'utf-8-sig', 'latin1', 'cp1258']
    
    for encoding in encodings:
        try:
            data = pd.read_csv(file_path, encoding=encoding, dtype=str)
            
            if data.shape[0] > 0 and data.shape[1] > 1:
                # Chỉ xử lý các cột triệu chứng (cột từ 1 trở đi)
                symptom_cols = data.columns[1:]
                data[symptom_cols] = data[symptom_cols].replace('[^0-9.]', '0', regex=True).astype(float)
                
                # Lưu cache để tăng tốc lần sau
                try:
                    data.to_pickle(cache_file)
                    print(f"Đã lưu dữ liệu vào cache để tăng tốc lần sau")
                except Exception as e:
                    print(f"Không thể lưu cache: {e}")
                
                print(f"Dữ liệu đã được tải thành công trong {time.time() - start_time:.2f} giây")
                print(f"Dữ liệu gồm {data.shape[0]} bệnh và {data.shape[1]-1} triệu chứng")
                return data
        except Exception as e:
            print(f"Thử với encoding {encoding} thất bại: {e}")
    
    print("Không thể tải dữ liệu. Vui lòng kiểm tra định dạng file.")
    return None


def preprocess_data(data):
    """
    Xử lý dữ liệu để chuẩn bị cho việc huấn luyện mô hình
    """
    # Lấy tên bệnh (cột đầu tiên)
    disease_names = data.iloc[:, 0].values
    
    # Lấy dữ liệu triệu chứng (các cột còn lại)
    symptoms_data = data.iloc[:, 1:].astype(float).values
    
    # Lấy tên các triệu chứng
    symptom_names = data.columns[1:].tolist()
    
    return disease_names, symptoms_data, symptom_names


def train_decision_tree(symptoms_data, disease_names):
    """
    Huấn luyện mô hình cây quyết định
    """
    # Kiểm tra dữ liệu đầu vào
    if len(symptoms_data) == 0 or len(disease_names) == 0:
        print("Lỗi: Dữ liệu đầu vào trống")
        return None
    
    start_time = time.time()
    print("Bắt đầu huấn luyện mô hình...")
    
    # Chia dữ liệu thành tập huấn luyện và tập kiểm tra
    X_train, X_test, y_train, y_test = train_test_split(
        symptoms_data, disease_names, test_size=0.2, random_state=42
    )
    
    # Khởi tạo và huấn luyện mô hình Decision Tree
    model = DecisionTreeClassifier(random_state=42)
    model.fit(X_train, y_train)
    
    # Đánh giá mô hình
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    
    print(f"Hoàn thành huấn luyện trong {time.time() - start_time:.2f} giây")
    print(f"Độ chính xác của mô hình: {accuracy:.2f}")
    
    return model


def predict_disease(model, symptom_input, symptom_names):
    """
    Dự đoán bệnh dựa trên các triệu chứng nhập vào
    """
    # Tạo mảng input dựa trên các triệu chứng được nhập
    input_data = np.zeros(len(symptom_names))
    
    for symptom in symptom_input:
        if symptom in symptom_names:
            idx = symptom_names.index(symptom)
            input_data[idx] = 1
    
    # Dự đoán bệnh
    input_data = input_data.reshape(1, -1)
    
    # Tính xác suất cho các bệnh
    disease_proba = model.predict_proba(input_data)[0]
    
    # Lấy chỉ số của các bệnh được sắp xếp theo xác suất giảm dần
    sorted_indices = np.argsort(disease_proba)[::-1]
    
    # Lấy tên và xác suất của các bệnh được sắp xếp
    sorted_diseases = [(model.classes_[i], disease_proba[i]) for i in sorted_indices]
    
    return sorted_diseases


def fuzzy_match(input_text, symptom_list, threshold=0.6):
    """
    Tìm triệu chứng phù hợp nhất với từ khóa nhập vào bằng so khớp mờ
    """
    from difflib import SequenceMatcher
    
    best_matches = []
    input_text = input_text.lower().strip()
    
    # Tìm các triệu chứng có độ tương đồng cao
    for symptom in symptom_list:
        similarity = SequenceMatcher(None, input_text, symptom.lower()).ratio()
        if similarity >= threshold:
            best_matches.append((symptom, similarity))
    
    # Sắp xếp theo độ tương đồng giảm dần
    best_matches.sort(key=lambda x: x[1], reverse=True)
    
    return best_matches


def search_symptoms(keyword, symptom_names):
    """
    Tìm kiếm triệu chứng dựa trên từ khóa
    """
    matches = fuzzy_match(keyword, symptom_names)
    return matches


def main():
    # Đọc dữ liệu
    file_path = "dataset.csv"
    data = load_data(file_path)
    
    if data is None or data.shape[0] == 0:
        print("Lỗi: Không có dữ liệu hợp lệ được tải")
        return
    
    # Xử lý dữ liệu
    disease_names, symptoms_data, symptom_names = preprocess_data(data)
    
    # Huấn luyện mô hình
    model = train_decision_tree(symptoms_data, disease_names)
    
    # Mảng lưu trữ các triệu chứng đã chọn trong phiên hiện tại
    selected_symptoms = []
    
    # Giao diện nhập triệu chứng và dự đoán bệnh
    while True:
        print("\n=== HỆ THỐNG DỰ ĐOÁN BỆNH TỪ TRIỆU CHỨNG ===")
        
        # Hiển thị triệu chứng đã chọn
        if selected_symptoms:
            print("\nCác triệu chứng hiện tại:", ", ".join(selected_symptoms))
        
        print("\nLựa chọn:")
        print("1. Tìm kiếm triệu chứng")
        print("2. Xem danh sách tất cả triệu chứng")
        print("3. Dự đoán bệnh với các triệu chứng đã chọn")
        print("4. Xóa tất cả triệu chứng đã chọn")
        print("5. Thoát")
        
        choice = input("\nNhập lựa chọn của bạn (1-5): ")
        
        if choice == '1':
            # Tìm kiếm triệu chứng
            keyword = input("Nhập từ khóa tìm kiếm triệu chứng: ")
            matches = search_symptoms(keyword, symptom_names)
            
            if matches:
                print("\nCác triệu chứng phù hợp:")
                for i, (symptom, similarity) in enumerate(matches[:10], 1):
                    print(f"{i}. {symptom} (Độ phù hợp: {similarity:.2f})")
                
                # Chọn triệu chứng từ kết quả tìm kiếm
                select = input("\nNhập số để chọn triệu chứng (hoặc 0 để quay lại): ")
                if select.isdigit() and 1 <= int(select) <= len(matches[:10]):
                    selected_symptom = matches[int(select)-1][0]
                    if selected_symptom not in selected_symptoms:
                        selected_symptoms.append(selected_symptom)
                        print(f"Đã thêm triệu chứng: {selected_symptom}")
                    else:
                        print(f"Triệu chứng '{selected_symptom}' đã được chọn từ trước!")
            else:
                print("Không tìm thấy triệu chứng phù hợp!")
                
        elif choice == '2':
            # Xem danh sách tất cả triệu chứng
            page_size = 20
            total_pages = (len(symptom_names) + page_size - 1) // page_size
            current_page = 1
            
            while True:
                start_idx = (current_page - 1) * page_size
                end_idx = min(start_idx + page_size, len(symptom_names))
                
                print(f"\nDanh sách triệu chứng (Trang {current_page}/{total_pages}):")
                for i, symptom in enumerate(symptom_names[start_idx:end_idx], start_idx + 1):
                    print(f"{i}. {symptom}")
                
                print("\nNhập 'p' để xem trang trước, 'n' để xem trang sau")
                print("Nhập số để chọn triệu chứng, hoặc 'q' để quay lại menu chính")
                
                select = input("Lựa chọn của bạn: ")
                
                if select.lower() == 'q':
                    break
                elif select.lower() == 'p' and current_page > 1:
                    current_page -= 1
                elif select.lower() == 'n' and current_page < total_pages:
                    current_page += 1
                elif select.isdigit() and 1 <= int(select) <= len(symptom_names):
                    idx = int(select) - 1
                    if symptom_names[idx] not in selected_symptoms:
                        selected_symptoms.append(symptom_names[idx])
                        print(f"Đã thêm triệu chứng: {symptom_names[idx]}")
                    else:
                        print(f"Triệu chứng '{symptom_names[idx]}' đã được chọn từ trước!")
                
        elif choice == '3':
            # Dự đoán bệnh với các triệu chứng đã chọn
            if not selected_symptoms:
                print("Vui lòng chọn ít nhất một triệu chứng trước khi dự đoán!")
                continue
                
            # Dự đoán bệnh
            disease_predictions = predict_disease(model, selected_symptoms, symptom_names)
            
            # Hiển thị kết quả
            print("\n=== KẾT QUẢ DỰ ĐOÁN ===")
            print("Các bệnh có thể mắc phải (sắp xếp theo xác suất giảm dần):")
            
            # Hiển thị top 5 bệnh có xác suất cao nhất
            for i, (disease, probability) in enumerate(disease_predictions[:5], 1):
                if probability > 0:
                    print(f"{i}. {disease}: {probability:.2%}")
                    
        elif choice == '4':
            # Xóa tất cả triệu chứng đã chọn
            selected_symptoms = []
            print("Đã xóa tất cả triệu chứng!")
            
        elif choice == '5':
            # Thoát
            break
            
        else:
            print("Lựa chọn không hợp lệ!")
    
    print("Cảm ơn bạn đã sử dụng hệ thống!")

if __name__ == "__main__":
    main()