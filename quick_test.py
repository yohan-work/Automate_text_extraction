#!/usr/bin/env python3
"""
웹 텍스트 추출 도구 간단 테스트 스크립트
"""

from cli_extractor import CLIWebTextExtractor
import os

def main():
    print("=== 웹 텍스트 추출 및 번역 도구 테스트 ===\n")
    
    # 테스트할 URL (예시)
    test_url = input("테스트할 URL을 입력하세요 (기본값: https://example.com): ").strip()
    if not test_url:
        test_url = "https://example.com"
    
    print(f"\n테스트 URL: {test_url}")
    
    # 번역 언어 선택
    print("\n번역 언어를 선택하세요:")
    print("1. 영어만")
    print("2. 영어 + 중국어")
    print("3. 영어 + 중국어 + 베트남어 (기본값)")
    print("4. 사용자 정의")
    
    choice = input("선택 (1-4): ").strip()
    
    if choice == "1":
        languages = ['en']
    elif choice == "2":
        languages = ['en', 'zh-cn']
    elif choice == "4":
        print("\n지원 언어 코드:")
        print("en (영어), zh-cn (중국어), vi (베트남어), ja (일본어)")
        print("es (스페인어), fr (프랑스어), de (독일어), ru (러시아어)")
        lang_input = input("언어 코드를 공백으로 구분하여 입력: ").strip()
        languages = lang_input.split() if lang_input else ['en', 'zh-cn', 'vi']
    else:
        languages = ['en', 'zh-cn', 'vi']
    
    print(f"\n선택된 번역 언어: {', '.join(languages)}")
    
    # 출력 파일명
    output_file = f"테스트_결과_{test_url.replace('https://', '').replace('http://', '').replace('/', '_')}.xlsx"
    
    print(f"출력 파일: {output_file}")
    print("\n처리 시작...\n")
    
    # 추출기 생성 및 실행
    extractor = CLIWebTextExtractor()
    
    try:
        success = extractor.process_url(test_url, output_file, languages, verbose=True)
        
        if success:
            print(f"\n🎉 테스트 완료!")
            print(f"📁 결과 파일: {output_file}")
            
            if os.path.exists(output_file):
                file_size = os.path.getsize(output_file)
                print(f"📊 파일 크기: {file_size:,} bytes")
                
                # 파일 열기 여부 확인
                open_file = input("\n생성된 엑셀 파일을 열어보시겠습니까? (y/n): ").strip().lower()
                if open_file in ['y', 'yes', 'ㅇ']:
                    try:
                        os.startfile(output_file)  # Windows용
                    except:
                        print(f"파일을 수동으로 열어주세요: {output_file}")
        else:
            print("\n❌ 테스트 실패")
            
    except Exception as e:
        print(f"\n❌ 오류 발생: {str(e)}")
    
    print("\n테스트 완료!")

if __name__ == "__main__":
    main() 