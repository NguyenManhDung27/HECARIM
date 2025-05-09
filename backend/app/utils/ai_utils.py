import pandas as pd
import numpy as np
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split
import os
import time
from difflib import SequenceMatcher

# Cache for model and symptom data
_cached_model = None
_cached_disease_names = None
_cached_symptom_names = None

def load_data(file_path):
    """
    Đọc dữ liệu từ file CSV với cải tiến tốc độ và tối ưu cho tệp lớn
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
            # Sử dụng chunking để đọc tệp lớn
            chunksize = 10000  # Đọc theo từng khối 10,000 dòng
            chunks = []
            
            print(f"Đang đọc file với encoding {encoding} và chunksize={chunksize}...")
            
            # Đọc từng khối dữ liệu
            for chunk in pd.read_csv(file_path, encoding=encoding, dtype=str, chunksize=chunksize):
                chunks.append(chunk)
            
            # Ghép các khối lại với nhau
            data = pd.concat(chunks, ignore_index=True)
            
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
    
    print(f"Hoàn thành huấn luyện trong {time.time() - start_time:.2f} giây")
    
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

def initialize_model():
    """
    Khởi tạo mô hình AI dự đoán bệnh với xử lý để không làm chặn server
    """
    global _cached_model, _cached_disease_names, _cached_symptom_names
    
    if _cached_model is not None and _cached_symptom_names is not None:
        return _cached_model, _cached_symptom_names
    
    try:
        print("Bắt đầu khởi tạo mô hình AI...")
        # Đường dẫn tới file dataset.csv
        file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), 
                                'AI', 'dataset.csv')
        
        # Kiểm tra tệp pickle cache đã tồn tại hay chưa
        cache_file = file_path + '.pickle'
        
        if not os.path.exists(file_path):
            print(f"CẢNH BÁO: Không tìm thấy file {file_path}")
            # Sử dụng file sample_dataset.csv thay thế
            file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), 
                                    'AI', 'sample_dataset.csv')
            print(f"Sử dụng file dự phòng: {file_path}")
            
            if not os.path.exists(file_path):
                print(f"LỖI: Không tìm thấy cả file dự phòng")
                return None, None
        
        # Load dữ liệu
        data = load_data(file_path)
        if data is None:
            print("Không thể tải dữ liệu AI.")
            return None, None
        
        # Xử lý dữ liệu
        disease_names, symptoms_data, symptom_names = preprocess_data(data)
        
        # Huấn luyện mô hình
        model = train_decision_tree(symptoms_data, disease_names)
        
        # Cache lại để sử dụng lần sau
        _cached_model = model
        _cached_disease_names = disease_names
        _cached_symptom_names = symptom_names
        
        print("Khởi tạo mô hình AI thành công!")
        return model, symptom_names
    except Exception as e:
        print(f"Lỗi khi khởi tạo mô hình AI: {e}")
        return None, None

def get_symptom_suggestions(keyword, top_n=10):
    """
    Tìm kiếm các triệu chứng phù hợp với từ khóa
    """
    _, symptom_names = initialize_model()
    
    if symptom_names is None:
        return []
    
    matches = fuzzy_match(keyword, symptom_names)
    
    # Giới hạn số kết quả trả về
    return [{"symptom": symptom, "similarity": round(similarity, 2)} 
            for symptom, similarity in matches[:top_n]]

def match_symptoms_from_text(symptom_inputs, threshold=0.6):
    """
    Tìm kiếm các triệu chứng phù hợp từ danh sách các chuỗi đầu vào
    """
    _, symptom_names = initialize_model()
    
    if symptom_names is None:
        print("Lỗi: Không thể lấy danh sách triệu chứng")
        return [], []
    
    matched_symptoms = []
    valid_inputs = []
    
    for input_text in symptom_inputs:
        if not input_text.strip():
            continue
            
        # Tìm triệu chứng phù hợp nhất
        matches = fuzzy_match(input_text, symptom_names, threshold)
        
        if matches:
            # Lấy triệu chứng có độ trùng khớp cao nhất
            best_match = matches[0][0]
            matched_symptoms.append(best_match)
            valid_inputs.append(input_text)
            print(f"Triệu chứng '{input_text}' được khớp với '{best_match}'")
        else:
            print(f"Không tìm thấy triệu chứng phù hợp cho '{input_text}'")
    
    return matched_symptoms, valid_inputs

def get_disease_prediction(symptoms):
    """
    Dự đoán bệnh dựa trên các triệu chứng
    """
    try:
        print(f"Dự đoán bệnh với các triệu chứng: {symptoms}")
        model, symptom_names = initialize_model()
        
        if model is None or symptom_names is None:
            print("Lỗi: model hoặc symptom_names là None")
            return []
        
        print(f"Tổng số triệu chứng có sẵn: {len(symptom_names)}")
        print(f"Các triệu chứng được nhận dạng: {[s for s in symptoms if s in symptom_names]}")
        
        predictions = predict_disease(model, symptoms, symptom_names)
        
        # Chỉ trả về các kết quả có xác suất > 0 và top 5 kết quả
        results = [{"disease": disease, "probability": round(probability * 100, 2)} 
                for disease, probability in predictions[:3] if probability > 0]
        
        print(f"Kết quả dự đoán: {results}")
        return results
    except Exception as e:
        import traceback
        print(f"Lỗi trong quá trình dự đoán bệnh: {e}")
        print(traceback.format_exc())
        return []
