import re

with open("src/frontend/app.py", "r") as f:
    content = f.read()

# We will just replace the specific tab2 section using regex or string replacement

old_section = """                        doc_col, data_col = st.columns(2)
                        with doc_col:
                            st.write("**Extracted Document Data**")
                            # Add scrollable div for extracted data so it doesn't take unlimited vertical space
                            if selected_item.get("error"):
                                st.error(f"Processing Error: {selected_item['error']}")
                            else:
                                data = selected_item["data"]
                                st.error("⚠️ REVIEW REQUIRED")
                                st.write("**Flags:**", data.get("flags", []))
                                st.write("**Extracted Data:**")
                                st.json(data.get("extracted_data"))
                                
                            if st.button("✅ Manual Sign-off (Approve Segment)", key=f"approve_{selected_item['filename']}"):
                                selected_item["status"] = "APPROVED"
                                st.session_state.review_selection = None
                                if hasattr(st, "rerun"):
                                    st.rerun()
                                else:
                                    st.experimental_rerun()
                                    
                        with data_col:
                            st.write("**Original Source Imagery**")
                            display_document(selected_item['filename'], selected_item['bytes'])"""

new_section = """                        doc_col, data_col = st.columns(2)
                        
                        with data_col:
                            st.subheader("Analysis Results")
                            # Add scrollable div for extracted data so it doesn't take unlimited vertical space
                            if selected_item.get("error"):
                                st.error(f"Processing Error: {selected_item['error']}")
                            else:
                                data = selected_item["data"]
                                st.error("⚠️ REVIEW REQUIRED")
                                st.write("**Flags:**", data.get("flags", []))
                                
                                if st.button("Manual Sign-off (Approve)", key=f"approve_{selected_item['filename']}"):
                                    selected_item["status"] = "APPROVED"
                                    st.session_state.review_selection = None
                                    if hasattr(st, "rerun"):
                                        st.rerun()
                                    else:
                                        st.experimental_rerun()
                                
                                st.write("**Extracted Data Structure:**")
                                st.json(data.get("extracted_data"))
                                    
                        with doc_col:
                            st.subheader("Original Source Imagery")
                            display_document(selected_item['filename'], selected_item['bytes'])"""

if old_section in content:
    content = content.replace(old_section, new_section)
    with open("src/frontend/app.py", "w") as f:
        f.write(content)
    print("Success")
else:
    print("Old section not found, replacement failed.")
