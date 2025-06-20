#!/usr/bin/env python3
"""
배치 URL 처리 도구
여러개의 URL을 한 번에 처리하여 각각 별도의 엑셀 파일로 저장하거나 하나의 파일에 통합
"""

import os
import csv
import json
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from cli_extractor import CLIWebTextExtractor

class BatchProcessor:
    def __init__(self, max_workers=3):
        self.extractor = CLIWebTextExtractor()
        self.max_workers = max_workers
        self.results = []
        self.lock = threading.Lock()
    
    def process_urls_from_file(self, input_file, output_dir="output", languages=['en', 'zh-cn', 'vi']):
        """파일에서 URL 목록을 읽어 배치 처리"""
        urls = self.read_urls_from_file(input_file)
        
        if not urls:
            print("URL을 찾을 수 없습니다.")
            return False
        
        return self.process_url_list(urls, output_dir, languages)
    
    def read_urls_from_file(self, file_path):
        """파일에서 URL 목록 읽기 (텍스트, CSV, JSON 지원)"""
        urls = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                file_ext = os.path.splitext(file_path)[1].lower()
                
                if file_ext == '.json':
                    data = json.load(f)
                    if isinstance(data, list):
                        urls = [item if isinstance(item, str) else item.get('url', '') for item in data]
                    elif isinstance(data, dict) and 'urls' in data:
                        urls = data['urls']
                
                elif file_ext == '.csv':
                    reader = csv.reader(f)
                    for row in reader:
                        if row and row[0].strip():  # 첫 번째 열이 URL이라고 가정
                            urls.append(row[0].strip())
                
                else:  # 일반 텍스트 파일
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):  # 주석 제외
                            urls.append(line)
        
        except Exception as e:
            print(f"파일 읽기 오류: {str(e)}")
            return []
        
        # URL 형식 검증 및 정리
        valid_urls = []
        for url in urls:
            if url:
                if not url.startswith(('http://', 'https://')):
                    url = 'https://' + url
                valid_urls.append(url)
        
        return valid_urls
    
    def process_url_list(self, urls, output_dir="output", languages=['en', 'zh-cn', 'vi']):
        """URL 목록 배치 처리"""
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        print(f"총 {len(urls)}개의 URL을 처리합니다...")
        print(f"번역 언어: {', '.join(languages)}")
        print(f"출력 디렉토리: {output_dir}")
        print(f"최대 동시 처리: {self.max_workers}개")
        print("-" * 50)
        
        successful = 0
        failed = 0
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 작업 제출
            future_to_url = {}
            for i, url in enumerate(urls, 1):
                output_file = os.path.join(output_dir, f"웹텍스트_{i:03d}_{self.url_to_filename(url)}.xlsx")
                future = executor.submit(self.process_single_url, url, output_file, languages, i, len(urls))
                future_to_url[future] = url
            
            # 결과 수집
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    result = future.result()
                    if result:
                        successful += 1
                    else:
                        failed += 1
                except Exception as e:
                    print(f"❌ {url} - 처리 중 예외 발생: {str(e)}")
                    failed += 1
        
        print("-" * 50)
        print(f"처리 완료! 성공: {successful}개, 실패: {failed}개")
        
        # 결과 리포트 생성
        self.generate_report(output_dir, successful, failed)
        
        return successful > 0
    
    def process_single_url(self, url, output_file, languages, current, total):
        """단일 URL 처리"""
        try:
            print(f"[{current}/{total}] 처리 시작: {url}")
            
            text_elements = self.extractor.extract_text_from_url(url, verbose=False)
            
            if not text_elements:
                print(f"❌ [{current}/{total}] 텍스트 추출 실패: {url}")
                return False
            
            success = self.extractor.create_excel_file(text_elements, output_file, languages, verbose=False)
            
            if success:
                print(f"✅ [{current}/{total}] 완료: {os.path.basename(output_file)}")
                
                # 결과 기록
                with self.lock:
                    self.results.append({
                        'url': url,
                        'output_file': output_file,
                        'text_count': len(text_elements),
                        'status': 'success',
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    })
                
                return True
            else:
                print(f"❌ [{current}/{total}] 엑셀 생성 실패: {url}")
                return False
                
        except Exception as e:
            print(f"❌ [{current}/{total}] 오류: {url} - {str(e)}")
            return False
    
    def url_to_filename(self, url):
        """URL을 파일명으로 변환"""
        # URL에서 도메인 추출
        from urllib.parse import urlparse
        parsed = urlparse(url)
        domain = parsed.netloc.replace('www.', '')
        
        # 파일명으로 사용할 수 없는 문자 제거
        safe_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
        filename = ''.join(c if c in safe_chars else '_' for c in domain)
        
        return filename[:30]  # 너무 긴 파일명 방지
    
    def generate_report(self, output_dir, successful, failed):
        """처리 결과 리포트 생성"""
        report_file = os.path.join(output_dir, f"처리결과_리포트_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
        
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write("웹 텍스트 추출 배치 처리 결과 리포트\n")
                f.write("=" * 50 + "\n")
                f.write(f"처리 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"성공: {successful}개\n")
                f.write(f"실패: {failed}개\n")
                f.write(f"총 처리: {successful + failed}개\n\n")
                
                if self.results:
                    f.write("상세 결과:\n")
                    f.write("-" * 30 + "\n")
                    for result in self.results:
                        f.write(f"URL: {result['url']}\n")
                        f.write(f"파일: {os.path.basename(result['output_file'])}\n")
                        f.write(f"텍스트 수: {result['text_count']}개\n")
                        f.write(f"상태: {result['status']}\n")
                        f.write(f"시간: {result['timestamp']}\n")
                        f.write("-" * 30 + "\n")
            
            print(f"📊 처리 리포트 생성: {report_file}")
            
        except Exception as e:
            print(f"리포트 생성 오류: {str(e)}")

def create_sample_url_file():
    """샘플 URL 파일 생성"""
    sample_urls = [
        "https://www.lgdisplay.com/kor/sustainability/esg-strategy",
        "https://news.naver.com",
        "https://www.korea.kr",
        "# 이것은 주석입니다",
        "https://example.com"
    ]
    
    # 텍스트 파일
    with open("sample_urls.txt", "w", encoding="utf-8") as f:
        for url in sample_urls:
            f.write(url + "\n")
    
    # JSON 파일
    json_data = {
        "urls": [url for url in sample_urls if not url.startswith("#")],
        "description": "웹 텍스트 추출을 위한 샘플 URL 목록"
    }
    
    with open("sample_urls.json", "w", encoding="utf-8") as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)
    
    # CSV 파일
    with open("sample_urls.csv", "w", encoding="utf-8", newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["URL", "설명"])
        writer.writerow(["https://www.lgdisplay.com/kor/sustainability/esg-strategy", "LG디스플레이 ESG"])
        writer.writerow(["https://news.naver.com", "네이버 뉴스"])
        writer.writerow(["https://www.korea.kr", "대한민국 정부"])
    
    print("📁 샘플 파일 생성 완료:")
    print("  - sample_urls.txt")
    print("  - sample_urls.json") 
    print("  - sample_urls.csv")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="배치 웹 텍스트 추출 및 번역 도구",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  python batch_processor.py urls.txt
  python batch_processor.py urls.json -o results -l en zh-cn
  python batch_processor.py urls.csv --workers 5
  python batch_processor.py --create-sample
        """
    )
    
    parser.add_argument('input_file', nargs='?', help='URL이 포함된 파일 (txt, json, csv)')
    parser.add_argument('-o', '--output-dir', default='output', 
                       help='출력 디렉토리 (기본값: output)')
    parser.add_argument('-l', '--languages', nargs='+', 
                       default=['en', 'zh-cn', 'vi'],
                       help='번역할 언어 코드 (기본값: en zh-cn vi)')
    parser.add_argument('-w', '--workers', type=int, default=3,
                       help='동시 처리 스레드 수 (기본값: 3)')
    parser.add_argument('--create-sample', action='store_true',
                       help='샘플 URL 파일들 생성')
    
    args = parser.parse_args()
    
    if args.create_sample:
        create_sample_url_file()
        return
    
    if not args.input_file:
        parser.print_help()
        return
    
    if not os.path.exists(args.input_file):
        print(f"❌ 파일을 찾을 수 없습니다: {args.input_file}")
        return
    
    processor = BatchProcessor(max_workers=args.workers)
    
    try:
        success = processor.process_urls_from_file(
            args.input_file,
            args.output_dir,
            args.languages
        )
        
        if success:
            print("🎉 배치 처리가 완료되었습니다!")
        else:
            print("❌ 배치 처리 중 오류가 발생했습니다.")
            
    except KeyboardInterrupt:
        print("\n⏹️ 작업이 사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")

if __name__ == "__main__":
    main() 